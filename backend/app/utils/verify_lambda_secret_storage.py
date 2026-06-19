"""
Verify whether sensitive secrets are still stored directly in Lambda environment variables.

This script is read-only. It prints secret variable names, never values.

Example:
    python -m app.utils.verify_lambda_secret_storage ^
      --region ap-south-1 ^
      --function-name ashmi-backend-dev ^
      --function-name ashmi-image-processor-dev
"""

import argparse
import re
import sys

import boto3


SENSITIVE_EXACT_KEYS = {
    "SECRET_KEY",
    "DATABASE_URL",
    "DATABASE_URL_SYNC",
    "SMTP_PASSWORD",
    "RAZORPAY_KEY_SECRET",
    "RAZORPAY_WEBHOOK_SECRET",
    "STRIPE_SECRET_KEY",
    "STRIPE_WEBHOOK_SECRET",
    "PII_ENCRYPTION_KEY",
    "IMAGE_CALLBACK_SECRET",
}

SENSITIVE_PATTERNS = [
    re.compile(r".*SECRET.*", re.IGNORECASE),
    re.compile(r".*PASSWORD.*", re.IGNORECASE),
    re.compile(r".*TOKEN.*", re.IGNORECASE),
    re.compile(r".*PRIVATE.*KEY.*", re.IGNORECASE),
    re.compile(r".*DATABASE_URL.*", re.IGNORECASE),
]


def is_sensitive_key(key: str) -> bool:
    if key in SENSITIVE_EXACT_KEYS:
        return True
    return any(pattern.fullmatch(key) for pattern in SENSITIVE_PATTERNS)


def verify_function(region: str, function_name: str, fail_on_env_secrets: bool) -> bool:
    client = boto3.client("lambda", region_name=region)

    response = client.get_function_configuration(FunctionName=function_name)
    env = response.get("Environment", {}).get("Variables", {})

    sensitive_keys = sorted(key for key in env if is_sensitive_key(key))

    if not sensitive_keys:
        print(f"OK: {function_name}: no sensitive-looking Lambda env vars found")
        return True

    print(f"FOUND: {function_name}: sensitive-looking Lambda env vars are present:")
    for key in sensitive_keys:
        print(f"  - {key}")

    if fail_on_env_secrets:
        print(f"FAILED: {function_name}: sensitive env vars should move to Secrets Manager/SSM")
        return False

    print(f"WARN: {function_name}: values are hidden, but these names indicate env-based secrets")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit Lambda environment variables for sensitive secret names."
    )
    parser.add_argument("--region", default="ap-south-1")
    parser.add_argument(
        "--function-name",
        action="append",
        required=True,
        help="Lambda function name. Pass multiple times for multiple functions.",
    )
    parser.add_argument(
        "--fail-on-env-secrets",
        action="store_true",
        help="Exit non-zero if sensitive env vars are found.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    all_ok = True
    for function_name in args.function_name:
        ok = verify_function(
            region=args.region,
            function_name=function_name,
            fail_on_env_secrets=args.fail_on_env_secrets,
        )
        all_ok = all_ok and ok

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())