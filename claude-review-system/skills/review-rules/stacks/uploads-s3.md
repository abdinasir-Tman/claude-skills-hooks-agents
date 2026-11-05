# Stack: uploads-s3 (multer, S3/R2, local file storage)

Detect: `multer`, `@aws-sdk/client-s3`, `busboy`, `formidable`.

## Discovery
- Upload middleware config (limits, fileFilter), storage target, how object keys are built, public vs presigned access.

## Security checks
- Size limits and file-count limits set; content type checked by sniffing or allow-list, not just extension/client MIME.
- Object keys / file paths built from server-controlled values (tenant/user IDs + generated names), never raw filenames (`..`, `/`).
- Private files served via presigned URLs with short expiry and an ownership check, not public buckets.
- SVG/HTML uploads not served inline from the app origin (stored XSS).
