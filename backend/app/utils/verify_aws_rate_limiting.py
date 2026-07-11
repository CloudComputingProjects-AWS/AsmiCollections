"""
Verify API Gateway throttling is configured for the deployed HTTP API stage.

Usage:
    python -m app.utils.verify_aws_rate_limiting

Required environment variables:
    AWS_REGION
    API_GATEWAY_ID
    API_GATEWAY_STAGE
    EXPECTED_API_THROTTLE_BURST
    EXPECTED_API_THROTTLE_RATE
"""

from __future__ import annotations

import os
import sys

import boto3


def _fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def verify_http_api_throttling() -> None:
    api_id = os.getenv("API_GATEWAY_ID", "").strip()
    if not api_id:
        _fail("API_GATEWAY_ID is not configured")

    stage_name = os.getenv("API_GATEWAY_STAGE", "").strip()
    if not stage_name:
        _fail("API_GATEWAY_STAGE is not configured")

    region = os.getenv("AWS_REGION", "").strip() or "ap-south-1"
    expected_burst = int(os.getenv("EXPECTED_API_THROTTLE_BURST", "0"))
    expected_rate = float(os.getenv("EXPECTED_API_THROTTLE_RATE", "0"))

    client = boto3.client("apigatewayv2", region_name=region)
    stage = client.get_stage(ApiId=api_id, StageName=stage_name)

    default_route_settings = stage.get("DefaultRouteSettings") or {}
    route_settings = stage.get("RouteSettings") or {}

    burst = default_route_settings.get("ThrottlingBurstLimit")
    rate = default_route_settings.get("ThrottlingRateLimit")
    has_default_throttle = burst is not None and rate is not None

    if not has_default_throttle and not any(route_settings.values()):
        _fail("No API Gateway throttling found on default route or route settings")

    if burst is not None and burst < expected_burst:
        _fail(f"Default burst throttle too low or unexpected: {burst}")

    if rate is not None and rate < expected_rate:
        _fail(f"Default rate throttle too low or unexpected: {rate}")

    print(f"Default stage throttling configured: burst={burst}, rate={rate}")

    if route_settings:
        print("Route-level throttling is configured")

    print(f"Verified API Gateway throttling for {api_id}/{stage_name}")


if __name__ == "__main__":
    verify_http_api_throttling()
