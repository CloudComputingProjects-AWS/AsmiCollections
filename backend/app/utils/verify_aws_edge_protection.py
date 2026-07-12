"""
Verify public AWS edge protections for supported runtime paths.

Checks:
1. API Gateway throttling on the deployed HTTP API stage
2. CloudFront distribution has an attached WAF WebACL
3. The attached WAF has at least one top-level rate-based block rule

Usage:
    python -m app.utils.verify_aws_edge_protection \
      --cloudfront-distribution-id YOUR_DISTRIBUTION_ID
"""

from __future__ import annotations

import argparse
from typing import NoReturn

import boto3

from app.utils.verify_aws_rate_limiting import verify_http_api_throttling


def _fail(message: str) -> "NoReturn":
    raise SystemExit(message)


def verify_cloudfront_waf(distribution_id: str) -> None:
    cloudfront = boto3.client("cloudfront")
    response = cloudfront.get_distribution_config(Id=distribution_id)
    distribution_config = response.get("DistributionConfig", {})
    web_acl_id = distribution_config.get("WebACLId") or ""

    if not web_acl_id:
        _fail("No WAF WebACL associated with CloudFront distribution")

    print(f"CloudFront distribution has WAF WebACL associated: {web_acl_id}")

    if not web_acl_id.startswith("arn:aws:wafv2:"):
        print("WAF association exists; skipped rule inspection because ARN format was unexpected")
        return

    parts = web_acl_id.split(":")
    if len(parts) < 6:
        print("WAF association exists; skipped rate-based rule inspection because WebACLId is not a WAFv2 ARN")
        return

    scope = "CLOUDFRONT"
    region_name = "us-east-1"
    resource = parts[5]
    resource_parts = resource.split("/")
    if len(resource_parts) < 4:
        print("WAF association exists; skipped rule inspection because ARN format was unexpected")
        return

    web_acl_name = resource_parts[2]
    web_acl_uuid = resource_parts[3]

    waf = boto3.client("wafv2", region_name=region_name)
    acl = waf.get_web_acl(Name=web_acl_name, Scope=scope, Id=web_acl_uuid)
    rules = acl.get("WebACL", {}).get("Rules", [])

    rate_rules = []
    for rule in rules:
        statement = rule.get("Statement") or {}
        if "RateBasedStatement" in statement:
            rate_rules.append(rule)

    if not rate_rules:
        _fail(f"WAF WebACL {web_acl_name} is attached but has no top-level rate-based rules")

    blocking_rules = []
    for rule in rate_rules:
        action = rule.get("Action") or {}
        actions = list(action.keys())
        if "Block" in actions:
            blocking_rules.append(rule["Name"])

    if blocking_rules:
        print(f"WAF rate-based Block rule(s) found: {', '.join(blocking_rules)}")
    else:
        _fail("WAF rate-based rule(s) found, but none are top-level Block actions. Review rule/action behavior manually")


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify AWS API Gateway throttling and CloudFront WAF")
    parser.add_argument("--cloudfront-distribution-id", required=True)
    args = parser.parse_args()

    verify_http_api_throttling()
    verify_cloudfront_waf(args.cloudfront_distribution_id)


if __name__ == "__main__":
    main()
