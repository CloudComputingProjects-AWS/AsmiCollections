"""
Unit Tests — Payment Service (Phase 8).

Run: pytest app/tests/test_payment_service.py -v
Status: Not runtime-verified. Adjust DB fixtures to match your test infra.
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.payment_service import PaymentService, PaymentServiceError


@pytest.fixture
def mock_db():
    db = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def payment_service(mock_db):
    return PaymentService(db=mock_db)


def make_mock_order(
    order_id=None, user_id=None, status="placed",
    payment_status="pending", grand_total=Decimal("2999.00"),
    currency="INR", payment_gateway=None, payment_gateway_txn_id=None,
    payment_gateway_order_id=None, order_number="ORD-20260216-0001",
):
    order = MagicMock()
    order.id = order_id or uuid4()
    order.user_id = user_id or uuid4()
    order.order_status = status
    order.payment_status = payment_status
    order.grand_total = grand_total
    order.currency = currency
    order.payment_gateway = payment_gateway
    order.payment_gateway_txn_id = payment_gateway_txn_id
    order.payment_gateway_order_id = payment_gateway_order_id
    order.order_number = order_number
    order.fx_rate_used = None
    return order


class TestGatewaySelection:
    def test_india_routes_to_razorpay(self, payment_service):
        result = payment_service.select_gateway("IN")
        assert result["gateway"] == "razorpay"
        assert "upi" in result["methods"]
        assert result["currency"] == "INR"

    def test_india_case_insensitive(self, payment_service):
        result = payment_service.select_gateway("in")
        assert result["gateway"] == "razorpay"

    def test_us_routes_to_stripe(self, payment_service):
        result = payment_service.select_gateway("US")
        assert result["gateway"] == "stripe"
        assert "credit_card" in result["methods"]

    def test_unknown_country_routes_to_stripe(self, payment_service):
        result = payment_service.select_gateway("ZZ")
        assert result["gateway"] == "stripe"


class TestRazorpayCreateOrder:
    @pytest.mark.asyncio
    async def test_rejects_non_placed_order(self, payment_service):
        user_id = uuid4()
        order = make_mock_order(user_id=user_id, status="confirmed")
        payment_service.repo.get_order = AsyncMock(return_value=order)

        with pytest.raises(PaymentServiceError, match="Cannot initiate payment"):
            await payment_service.create_razorpay_order(order_id=order.id, user_id=user_id)

    @pytest.mark.asyncio
    async def test_rejects_wrong_user(self, payment_service):
        order = make_mock_order()
        payment_service.repo.get_order = AsyncMock(return_value=order)

        with pytest.raises(PaymentServiceError, match="does not belong"):
            await payment_service.create_razorpay_order(order_id=order.id, user_id=uuid4())

    @pytest.mark.asyncio
    async def test_rejects_already_paid(self, payment_service):
        user_id = uuid4()
        order = make_mock_order(user_id=user_id, payment_status="paid")
        payment_service.repo.get_order = AsyncMock(return_value=order)

        with pytest.raises(PaymentServiceError, match="already in"):
            await payment_service.create_razorpay_order(order_id=order.id, user_id=user_id)


class TestWebhookIdempotency:
    @pytest.mark.asyncio
    async def test_duplicate_razorpay_event_skipped(self, payment_service):
        existing_event = MagicMock()
        existing_event.processed = True
        payment_service.repo.find_payment_event = AsyncMock(return_value=existing_event)

        result = await payment_service.process_razorpay_webhook({
            "event": "payment.captured",
            "payload": {"payment": {"entity": {"id": "pay_duplicate_123"}}},
        })
        assert result["status"] == "duplicate"


class TestRefundInitiation:
    @pytest.mark.asyncio
    async def test_rejects_unpaid_order(self, payment_service):
        order = make_mock_order(payment_status="pending")
        payment_service.repo.get_order = AsyncMock(return_value=order)

        with pytest.raises(PaymentServiceError, match="Cannot refund"):
            await payment_service.initiate_refund(
                order_id=order.id, amount=None, reason="Test refund", admin_id=uuid4(),
            )

    @pytest.mark.asyncio
    async def test_rejects_missing_gateway_info(self, payment_service):
        order = make_mock_order(payment_status="paid", payment_gateway=None)
        payment_service.repo.get_order = AsyncMock(return_value=order)

        with pytest.raises(PaymentServiceError, match="no payment gateway"):
            await payment_service.initiate_refund(
                order_id=order.id, amount=None, reason="Test refund", admin_id=uuid4(),
            )


class TestFXRateService:
    @pytest.mark.asyncio
    async def test_same_currency_returns_identity(self):
        from app.services.fx_rate_service import FXRateService
        svc = FXRateService()
        rate, source, _ = await svc.get_rate("USD", "USD")
        assert rate == Decimal("1.0")
        assert source == "identity"
