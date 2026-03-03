/**
 * AWS Lambda Image Processor — V2.5
 * 
 * Triggered by S3 PutObject event on uploads/raw/ prefix.
 * Generates 3 WebP variants using Sharp:
 *   - processed (1200px, quality 85) → /uploads/processed/{product_id}/{uuid}.webp
 *   - medium (800px, quality 85)     → /uploads/processed/{product_id}/{uuid}_800.webp
 *   - thumbnail (300px, quality 80)  → /uploads/processed/{product_id}/{uuid}_300.webp
 * 
 * Then POSTs callback to backend API to update product_images record.
 * 
 * Deploy: zip with node_modules (sharp requires native binaries for Lambda)
 *   npm install sharp @aws-sdk/client-s3
 *   Package for Lambda: use amazon-linux compatible sharp build
 */

const sharp = require('sharp');
const { S3Client, GetObjectCommand, PutObjectCommand } = require('@aws-sdk/client-s3');
const https = require('https');
const http = require('http');

const s3 = new S3Client({ region: process.env.AWS_REGION || 'ap-south-1' });

const SIZES = [
  { suffix: '',     width: 1200, quality: 85 },  // processed (full)
  { suffix: '_800', width: 800,  quality: 85 },  // medium
  { suffix: '_300', width: 300,  quality: 80 },  // thumbnail
];

const CALLBACK_URL = process.env.CALLBACK_URL || 'http://localhost:8000/api/v1/admin/images/callback';
const CLOUDFRONT_DOMAIN = process.env.CLOUDFRONT_DOMAIN || '';

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event, null, 2));

  for (const record of event.Records) {
    const bucket = record.s3.bucket.name;
    const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));

    // Only process files in uploads/raw/
    if (!key.startsWith('uploads/raw/')) {
      console.log(`Skipping non-raw key: ${key}`);
      continue;
    }

    // Extract product_id and filename from key
    // Format: uploads/raw/{product_id}/{uuid}.{ext}
    const parts = key.split('/');
    if (parts.length < 4) {
      console.error(`Invalid key format: ${key}`);
      continue;
    }

    const productId = parts[2];
    const originalFilename = parts[3];
    const nameWithoutExt = originalFilename.replace(/\.[^.]+$/, '');

    // Extract image_id from the database record
    // The image_id is embedded in the filename (uuid part)
    const imageId = nameWithoutExt; // This is the UUID used when creating the presigned URL

    try {
      // 1. Fetch original from S3
      console.log(`Fetching: s3://${bucket}/${key}`);
      const getResult = await s3.send(new GetObjectCommand({ Bucket: bucket, Key: key }));
      const inputBuffer = await streamToBuffer(getResult.Body);
      console.log(`Original size: ${(inputBuffer.length / 1024).toFixed(1)}KB`);

      const processedUrls = {};

      // 2. Generate each variant
      for (const size of SIZES) {
        const outputKey = `uploads/processed/${productId}/${nameWithoutExt}${size.suffix}.webp`;

        const processedBuffer = await sharp(inputBuffer)
          .resize(size.width, null, {
            fit: 'inside',
            withoutEnlargement: true,
          })
          .webp({ quality: size.quality })
          .toBuffer();

        console.log(`Generated ${size.suffix || 'full'}: ${(processedBuffer.length / 1024).toFixed(1)}KB (${size.width}px)`);

        // 3. Upload processed variant to S3
        await s3.send(new PutObjectCommand({
          Bucket: bucket,
          Key: outputKey,
          Body: processedBuffer,
          ContentType: 'image/webp',
          CacheControl: 'public, max-age=31536000, immutable',
        }));

        // Build URL (CloudFront or S3 direct)
        const baseUrl = CLOUDFRONT_DOMAIN
          ? `https://${CLOUDFRONT_DOMAIN}`
          : `https://${bucket}.s3.amazonaws.com`;

        if (size.suffix === '') {
          processedUrls.processed_url = `${baseUrl}/${outputKey}`;
        } else if (size.suffix === '_800') {
          processedUrls.medium_url = `${baseUrl}/${outputKey}`;
        } else if (size.suffix === '_300') {
          processedUrls.thumbnail_url = `${baseUrl}/${outputKey}`;
        }
      }

      // 4. POST callback to backend API
      console.log('Sending callback to:', CALLBACK_URL);
      await postCallback({
        image_id: imageId,
        processed_url: processedUrls.processed_url,
        medium_url: processedUrls.medium_url,
        thumbnail_url: processedUrls.thumbnail_url,
        status: 'completed',
      });

      console.log(`Successfully processed: ${key}`);

    } catch (error) {
      console.error(`Error processing ${key}:`, error);

      // Send failure callback
      try {
        await postCallback({
          image_id: imageId,
          processed_url: '',
          medium_url: '',
          thumbnail_url: '',
          status: 'failed',
        });
      } catch (callbackError) {
        console.error('Failed to send failure callback:', callbackError);
      }
    }
  }

  return { statusCode: 200, body: 'Processing complete' };
};

// ──────────── Helpers ────────────

async function streamToBuffer(stream) {
  const chunks = [];
  for await (const chunk of stream) {
    chunks.push(chunk);
  }
  return Buffer.concat(chunks);
}

async function postCallback(data) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(data);
    const url = new URL(CALLBACK_URL);
    const transport = url.protocol === 'https:' ? https : http;

    const options = {
      hostname: url.hostname,
      port: url.port || (url.protocol === 'https:' ? 443 : 80),
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(body),
      },
    };

    const req = transport.request(options, (res) => {
      let responseBody = '';
      res.on('data', (chunk) => { responseBody += chunk; });
      res.on('end', () => {
        console.log(`Callback response: ${res.statusCode} ${responseBody}`);
        resolve({ statusCode: res.statusCode, body: responseBody });
      });
    });

    req.on('error', reject);
    req.write(body);
    req.end();
  });
}
