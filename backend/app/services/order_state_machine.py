"""
Order State Machine — V2.5
Enforces legal order status transitions. Prevents illegal state changes.
"""

from enum import Enum


class OrderStatus(str, Enum):
    PLACED = "placed"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    RETURN_REQUESTED = "return_requested"
    RETURN_APPROVED = "return_approved"
    RETURN_REJECTED = "return_rejected"
    RETURN_RECEIVED = "return_received"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


# Legal transitions map
ORDER_TRANSITIONS: dict[str, list[str]] = {
    OrderStatus.PLACED:            [OrderStatus.CONFIRMED, OrderStatus.CANCELLED],
    OrderStatus.CONFIRMED:         [OrderStatus.PROCESSING, OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.PROCESSING:        [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED:           [OrderStatus.OUT_FOR_DELIVERY],
    OrderStatus.OUT_FOR_DELIVERY:  [OrderStatus.DELIVERED],
    OrderStatus.DELIVERED:         [OrderStatus.RETURN_REQUESTED],
    OrderStatus.RETURN_REQUESTED:  [OrderStatus.RETURN_APPROVED, OrderStatus.RETURN_REJECTED],
    OrderStatus.RETURN_APPROVED:   [OrderStatus.RETURN_RECEIVED],
    OrderStatus.RETURN_RECEIVED:   [OrderStatus.REFUNDED],
    OrderStatus.CANCELLED:         [],  # terminal
    OrderStatus.REFUNDED:          [],  # terminal
    OrderStatus.RETURN_REJECTED:   [],  # terminal
}

# Side effects triggered per transition
TRANSITION_SIDE_EFFECTS: dict[str, list[str]] = {
    OrderStatus.CONFIRMED:       ["reserve_stock", "send_confirmation_email", "generate_invoice"],
    OrderStatus.PROCESSING:      ["notify_warehouse"],
    OrderStatus.SHIPPED:         ["create_shipment", "send_shipping_email"],
    OrderStatus.OUT_FOR_DELIVERY: ["send_out_for_delivery_sms"],
    OrderStatus.DELIVERED:       ["send_delivery_email"],
    OrderStatus.RETURN_APPROVED: ["schedule_pickup", "send_return_approved_email"],
    OrderStatus.RETURN_RECEIVED: ["inspect_and_restock"],
    OrderStatus.REFUNDED:        ["process_refund", "generate_credit_note", "restock_inventory"],
    OrderStatus.CANCELLED:       ["release_stock", "process_refund_if_paid", "send_cancellation_email"],
}

TERMINAL_STATES = {OrderStatus.CANCELLED, OrderStatus.REFUNDED, OrderStatus.RETURN_REJECTED}


class OrderStateMachineError(Exception):
    """Raised when an illegal state transition is attempted."""

    def __init__(self, current_status: str, new_status: str):
        self.current_status = current_status
        self.new_status = new_status
        super().__init__(
            f"Illegal order transition: {current_status} → {new_status}. "
            f"Allowed from '{current_status}': {ORDER_TRANSITIONS.get(current_status, [])}"
        )


def can_transition(current_status: str, new_status: str) -> bool:
    """Check if a transition is legal."""
    allowed = ORDER_TRANSITIONS.get(current_status, [])
    return new_status in allowed


def validate_transition(current_status: str, new_status: str) -> None:
    """Validate and raise if illegal."""
    if not can_transition(current_status, new_status):
        raise OrderStateMachineError(current_status, new_status)


def get_side_effects(new_status: str) -> list[str]:
    """Get list of side effects to execute for a given transition target."""
    return TRANSITION_SIDE_EFFECTS.get(new_status, [])


def get_allowed_transitions(current_status: str) -> list[str]:
    """Get list of statuses the order can transition to from current."""
    return ORDER_TRANSITIONS.get(current_status, [])


def is_terminal(status: str) -> bool:
    """Check if the status is a terminal (final) state."""
    return status in TERMINAL_STATES


def is_cancellable(status: str) -> bool:
    """Check if order can be cancelled from current status."""
    return OrderStatus.CANCELLED in ORDER_TRANSITIONS.get(status, [])
