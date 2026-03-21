"""
AWS Lambda Image Processor — Python
Triggered by S3 PutObject event on uploads/raw/ prefix.

Generates 3 WebP variants using Pillow:
  - processed (1200px, quality 85) -> /uploads/processed/{product_id}/{uuid}.webp
  - medium (800px, quality 85)     -> /uploads/processed/{product_id}/{uuid}_800.webp
  - thumbnail (300px, quality 80)  -> /uploads/processed/{product_id}/{uuid}_300.webp

Then POSTs callback to backend API to update product_images record.

Backend callback endpoint: POST /api/v1/admin/images/callback
  Body: { image_id, processed_url, medium_url, thumbnail_url, status }
  No auth required (protected by API key/VPC in production).

Deploy as container image or zip with Pillow layer.
"""

import io
import json
import os
import urllib.parse
import urllib.request
from typing import Any

import boto3
from PIL import Image

# --------------- Configuration ---------------

AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
CALLBACK_URL = os.environ.get(
    "CALLBACK_URL",
    "https://9amq4q9qa4.execute-api.ap-south-1.amazonaws.com/api/v1/admin/images/callback",
)
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN", "")

SIZES = [
    {"suffix": "", "width": 1200, "quality": 85},       # processed (full)
    {"suffix": "_800", "width": 800, "quality": 85},     # medium
    {"suffix": "_300", "width": 300, "quality": 80},     # thumbnail
]

s3_client = boto3.client("s3", region_name=AWS_REGION)


# --------------- Handler ---------------

def lambda_handler(event: dict, context: Any) -> dict:
    """Main Lambda entry point — processes S3 event records."""
    print(f"Event: {json.dumps(event)}")

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])

        # Only process files in uploads/raw/
        if not key.startswith("uploads/raw/"):
            print(f"Skipping non-raw key: {key}")
            continue

        # Extract product_id and filename from key
        # Format: uploads/raw/{product_id}/{uuid}.{ext}
        parts = key.split("/")
        if len(parts) < 4:
            print(f"Invalid key format: {key}")
            continue

        product_id = parts[2]
        original_filename = parts[3]
        name_without_ext = original_filename.rsplit(".", 1)[0]

        # image_id is the UUID portion of the filename
        image_id = name_without_ext

        try:
            # 1. Fetch original from S3
            print(f"Fetching: s3://{bucket}/{key}")
            response = s3_client.get_object(Bucket=bucket, Key=key)
            input_bytes = response["Body"].read()
            print(f"Original size: {len(input_bytes) / 1024:.1f}KB")

            # Open image with Pillow
            original_image = Image.open(io.BytesIO(input_bytes))

            # Convert to RGB if necessary (e.g., RGBA PNG, CMYK)
            if original_image.mode in ("RGBA", "P"):
                # Preserve transparency by compositing on white background
                background = Image.new("RGB", original_image.size, (255, 255, 255))
                if original_image.mode == "P":
                    original_image = original_image.convert("RGBA")
                background.paste(original_image, mask=original_image.split()[3])
                original_image = background
            elif original_image.mode != "RGB":
                original_image = original_image.convert("RGB")

            processed_urls = {}

            # 2. Generate each variant
            for size in SIZES:
                output_key = (
                    f"uploads/processed/{product_id}/"
                    f"{name_without_ext}{size['suffix']}.webp"
                )

                # Resize maintaining aspect ratio, don't enlarge
                img_copy = original_image.copy()
                orig_width, orig_height = img_copy.size
                target_width = size["width"]

                if orig_width > target_width:
                    ratio = target_width / orig_width
                    target_height = int(orig_height * ratio)
                    img_copy = img_copy.resize(
                        (target_width, target_height), Image.LANCZOS
                    )

                # Save as WebP to buffer
                buffer = io.BytesIO()
                img_copy.save(buffer, format="WEBP", quality=size["quality"])
                buffer.seek(0)
                processed_bytes = buffer.getvalue()

                suffix_label = size["suffix"] if size["suffix"] else "full"
                resized_w, resized_h = img_copy.size
                print(
                    f"Generated {suffix_label}: "
                    f"{len(processed_bytes) / 1024:.1f}KB "
                    f"({resized_w}x{resized_h}px)"
                )

                # 3. Upload processed variant to S3
                s3_client.put_object(
                    Bucket=bucket,
                    Key=output_key,
                    Body=processed_bytes,
                    ContentType="image/webp",
                    CacheControl="public, max-age=31536000, immutable",
                )

                # Build URL (CloudFront or S3 direct)
                if CLOUDFRONT_DOMAIN:
                    base_url = f"https://{CLOUDFRONT_DOMAIN}"
                else:
                    base_url = f"https://{bucket}.s3.amazonaws.com"

                url = f"{base_url}/{output_key}"

                if size["suffix"] == "":
                    processed_urls["processed_url"] = url
                elif size["suffix"] == "_800":
                    processed_urls["medium_url"] = url
                elif size["suffix"] == "_300":
                    processed_urls["thumbnail_url"] = url

            # 4. POST callback to backend API
            print(f"Sending callback to: {CALLBACK_URL}")
            callback_data = {
                "image_id": image_id,
                "processed_url": processed_urls["processed_url"],
                "medium_url": processed_urls["medium_url"],
                "thumbnail_url": processed_urls["thumbnail_url"],
                "status": "completed",
            }
            _post_callback(callback_data)
            print(f"Successfully processed: {key}")

        except Exception as e:
            print(f"Error processing {key}: {e}")

            # Send failure callback
            try:
                _post_callback(
                    {
                        "image_id": image_id,
                        "processed_url": "",
                        "medium_url": "",
                        "thumbnail_url": "",
                        "status": "failed",
                    }
                )
            except Exception as callback_err:
                print(f"Failed to send failure callback: {callback_err}")

    return {"statusCode": 200, "body": "Processing complete"}


# --------------- Helpers ---------------

def _post_callback(data: dict) -> None:
    """POST JSON callback to the backend API."""
    body = json.dumps(data).encode("utf-8")

    req = urllib.request.Request(
        CALLBACK_URL,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(req, timeout=30) as resp:
        response_body = resp.read().decode("utf-8")
        print(f"Callback response: {resp.status} {response_body}")
