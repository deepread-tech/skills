# DeepRead API Reference

**Base URL:** `https://api.deepread.tech` | **Auth:** `X-API-Key` header

## Agent Authentication (Device Flow — RFC 8628)

**POST /v1/agent/device/code** — Auth: None. Body: `{"agent_name": "my-agent"}`
Response: `device_code` (secret), `user_code`, `verification_uri_complete`, `expires_in: 900`, `interval: 5`

**POST /v1/agent/device/token** — Auth: None. Body: `{"device_code": "..."}`
Poll every `interval` seconds:

| `error` | `api_key` | Action |
|---------|-----------|--------|
| `"authorization_pending"` | `null` | Wait, poll again |
| `null` | `"sk_live_..."` | Save immediately (returned once), stop |
| `"access_denied"` | `null` | Stop, inform user |
| `"expired_token"` | `null` | Restart from /device/code |

Never show `device_code` or `api_key` to the user.

## Processing

**POST /v1/process** — Auth: `X-API-Key`. Content-Type: `multipart/form-data`

| Param | Req | Default | Description |
|-------|-----|---------|-------------|
| `file` | Yes | — | PDF, PNG, JPEG on every plan; Standard adds TIFF, WebP, BMP, GIF, DOCX, TXT; Enterprise adds office, spreadsheet and HTML formats (415 if your plan lacks the type) |
| `pipeline` | No | plan default | Engine: `"extract"` (one OCR pass) or `"deep-extract"` (two passes, an LLM judge, and a second read that checks each extracted field value). Default: Free/Standard `extract`, Enterprise `deep-extract`. Aliases still accepted: `fast` = extract, `standard` = deep-extract, `searchable` = deep-extract + `searchable_pdf=true`; responses show the name you sent |
| `schema` | No | — | JSON Schema string for structured extraction |
| `blueprint_id` | No | — | UUID (mutually exclusive with schema) |
| `preview` | No | `"false"` | Page images + public preview link + each field located (`location.bounding_box`). Off unless `"true"`: the link is public. Replaces `include_images` (deprecated, honoured). Free plan: no preview link or stored images, locations still returned |
| `per_page` | No | `"false"` | Per-page breakdown. Replaces `include_pages` (deprecated, honoured) |
| `webhook_url` | No | — | HTTPS completion callback, signed (Standard and up; 402 on Free) |
| `idempotency_key` | No | — | ≤255 chars, unique per account. Same key → the same job (200); same key + different file/options → 409 |
| `searchable_pdf` | No | `"false"` | `"true"` → also make a searchable PDF. Deep Extract add-on: `deep-extract` only, Enterprise |
| `incognito` | No | `"false"` | Enterprise. `"true"` → document never stored in the clear, crypto-shredded when the job finishes (no preview link, no field locations; not with `searchable_pdf`; results unaffected) |
| `retention_days` | No | — | Enterprise. integer 1–365 → document, preview artifacts and results deleted N days after submission (content absent + preview 410 from the deadline on; `data_deleted_at` confirms) |
| `version` | No | — | Pipeline version pin |

Every job reports `product`: `parse` (extract, no schema), `extract` (extract + schema/blueprint), `deep-extract` (deep-extract, schema or not). `include_markers` is deprecated but honoured as an on/off override for locating.

Response: `{"id": "uuid", "status": "queued"}`
Errors: 400 (bad schema/file, Free doc over 50 pages), 401 (bad key), 402 (feature not on plan, or credits do not cover the job), 409 (idempotency key reused with a different request), 413 (over the plan file size or the hard max: 2,000 pages / 500 MB), 415 (file type not on plan), 429 (rate, pages in flight, or Free quota; `Retry-After`)

**GET /v1/jobs/{job_id}** — Auth: `X-API-Key`. Poll: wait 5s, then 5-10s backoff (max 5 min).
Statuses: `queued` → `processing` → `completed` | `failed`

Completed (dp02 — every response has `schema_version: "dp02"`): `{id, status, schema_version, pipeline, product, searchable_pdf, incognito, retention_expires_at (only with retention_days, until deletion), data_deleted_at (after the retention purge), document: {page_count, content: {format, text, text_preview, text_url (>1MB)}, layout}, extraction: {fields: [{key, value, needs_review, review_reason?, location: {page, bounding_box}}]}, pages (with `per_page=true`): [{page_number, content: {format, text}, fields, needs_review}], review: {needs_review, quality_score, fields_total, fields_needing_review, review_rate, flags}, artifacts: {preview_url, searchable_pdf_url}, webhook: {url, delivered, delivered_at, error}}`

**GET /v1/preview/{token}** — Auth: None. Public shareable preview.
**GET /v1/pipelines** — Auth: None. Engines and products with prices: `extract` (one pass; Parse $10 / 1,000 pages without a schema, Extract $20 with one) | `deep-extract` (two passes, judged, verification read, ~45-60s; Deep Extract $40). Searchable PDF = `deep-extract` + `searchable_pdf=true` add-on (Enterprise; not a tier).

## Blueprints & Optimizer

**GET /v1/blueprints/** — List blueprints (Auth: API key)
**GET /v1/blueprints/{id}** — Details with versions and accuracy metrics

**POST /v1/optimize** — Auth: API key. Fields: `name`, `document_type`, `training_documents` (min 2), `ground_truth_data`, `target_accuracy`, `max_iterations`, `max_cost_usd`. `initial_schema` optional (auto-generated). Response: `{job_id, blueprint_id, status}`

**POST /v1/optimize/resume** — Resume failed optimization
**GET /v1/blueprints/jobs/{id}** — Progress: `{status, iteration, current_accuracy, total_cost}`
**GET /v1/blueprints/jobs/{id}/schema** — Optimized schema after completion

## Webhooks

Add `webhook_url` to POST /v1/process (Standard and up; 402 on Free). The payload is identical to the `GET /v1/jobs/{id}` dp02 response (job identifier is `id`, not `job_id`; carries `schema_version: "dp02"`). Every delivery is signed: `X-DeepRead-Signature: t=<unix seconds>,v1=<hex>`, HMAC-SHA256 over `"<t>.<raw body>"` keyed by your account's secret (`GET /dashboard/v1/webhooks/secret`; rotate with `POST /dashboard/v1/webhooks/secret/rotate`). Verify over the exact bytes, compare in constant time, reject `t` older than 5 minutes. A verified payload needs no re-fetch. Return 2xx within 30s (non-2xx is retried with backoff). Design for idempotency.

```python
import hmac, hashlib, time

def verify(secret: str, header: str, body: bytes, tolerance: int = 300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    t = int(parts["t"])
    if abs(time.time() - t) > tolerance:
        return False
    expected = hmac.new(secret.encode(), f"{t}.".encode() + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, parts["v1"])
```

## Rate Limits & Plans

| Plan | Pages | Per doc | Max file | File types | Submits/min | Pages in flight |
|------|-------|---------|----------|------------|-------------|-----------------|
| Free | 2,000/month, resets on your signup day | 50 pages | 15 MB | PDF, PNG, JPEG | 10 | 16 |
| Standard | Prepaid credits from $10 per 1,000 pages (Parse $10, Extract $20, Deep Extract $40); no page limits | — | 50 MB | + TIFF, WebP, BMP, GIF, DOCX, TXT | 100 | 200 |
| Enterprise | Custom | — | 500 MB | + APNG, PSD, PCX, PPM, CUR, DCX, FTEX, PIXAR, DOC, DOTX, ODT, RTF, WPD, PPT, PPTX, ODP, HTML, CSV, XLSX, XLSM, XLS, XLTX, XLTM, ODS | 500 | 500 |

Enterprise adds searchable PDF, retention, incognito, PII redaction, form fill, BYOK. Webhooks, blueprints, optimizer: Standard and up. Pro/Scale/BYOK are legacy account names, not plans. Submits over the minute → 429 + `Retry-After`. Pages in flight = pages of queued + processing jobs; over the cap → 429, `Retry-After: 30`, body `{pages_in_flight, max_pages_in_flight, pages_requested}` (admission limit, nothing queued). Hard max for everyone: 2,000 pages / 500 MB → 413. File type not on plan → 415 naming the plan. Polling GET /v1/jobs: Free 20/min, Standard 60, Enterprise 150. Retry safely with `idempotency_key`.

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Used`, `X-RateLimit-Reset`

## Errors — `{"detail": "message"}`

400 (bad schema/file/both schema+blueprint) | 401 (bad key) | 402 (feature not on plan, or credits) | 404 (not found) | 409 (idempotency key reused) | 413 (too large) | 415 (file type not on plan) | 429 (rate/in-flight/quota, `Retry-After`) | 500 (server)

## Code Examples

### Python
```python
import requests, time, json
API_KEY, BASE = "sk_live_YOUR_KEY", "https://api.deepread.tech"
schema = {"type":"object","properties":{"vendor":{"type":"string","description":"Vendor name"},"total":{"type":"number","description":"Total amount due"}}}
with open("invoice.pdf","rb") as f:
    job_id = requests.post(f"{BASE}/v1/process", headers={"X-API-Key":API_KEY},
        files={"file":f}, data={"schema":json.dumps(schema)}).json()["id"]
delay = 5
while True:
    time.sleep(delay)
    r = requests.get(f"{BASE}/v1/jobs/{job_id}", headers={"X-API-Key":API_KEY}).json()
    if r["status"] in ("completed","failed"): break
    delay = min(delay*1.5, 30)
```

### JavaScript
```javascript
import fs from "fs";
const form = new FormData();
form.append("file", fs.createReadStream("invoice.pdf"));
form.append("schema", JSON.stringify({type:"object",properties:{vendor:{type:"string",description:"Vendor name"}}}));
const {id:jobId} = await fetch("https://api.deepread.tech/v1/process",
  {method:"POST", headers:{"X-API-Key":"sk_live_YOUR_KEY"}, body:form}).then(r=>r.json());
let delay=5000, result;
do {
  await new Promise(r=>setTimeout(r,delay));
  result = await fetch(`https://api.deepread.tech/v1/jobs/${jobId}`,{headers:{"X-API-Key":"sk_live_YOUR_KEY"}}).then(r=>r.json());
  delay = Math.min(delay*1.5,30000);
} while(!["completed","failed"].includes(result.status));
```

### cURL
```bash
curl -X POST https://api.deepread.tech/v1/process -H "X-API-Key: YOUR_KEY" \
  -F "file=@invoice.pdf" -F 'schema={"type":"object","properties":{"vendor":{"type":"string","description":"Vendor name"}}}'
curl https://api.deepread.tech/v1/jobs/JOB_ID -H "X-API-Key: YOUR_KEY"
```

**Quick ref:** No key → device flow (see deepread-setup) | Submit → POST /v1/process | Results → GET /v1/jobs/{id} | Engine → `pipeline=extract` or `deep-extract` | Structured → `schema` | Better accuracy → `blueprint_id` | Share → `artifacts.preview_url` | HIL → filter `extraction.fields[]` by `needs_review: true`
