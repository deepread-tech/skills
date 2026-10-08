# DeepRead PII Removal API Reference

**Base URL:** `https://api.deepread.tech` | **Auth:** `X-API-Key` header

## What It Does

Upload a document (PDF, text, image). AI detects 14 types of PII automatically, redacts them, returns a clean document with detection report. Works with any supported format — no configuration needed.

**PII types:** SSN, credit cards, emails, phone numbers, names, addresses, dates of birth, passport numbers, driver's licenses, bank accounts, IBANs, IP addresses, URLs, medical record numbers.

**Redaction styles:** `black_bar` (default, black rectangles), `placeholder` (type labels like `[NAME]`), `partial` (reveal last digits like `***-**-6789`)

## POST /v1/pii/redact — Submit for Redaction

**Auth:** `X-API-Key`. Content-Type: `multipart/form-data`

| Param | Req | Default | Description |
|-------|-----|---------|-------------|
| `file` | Yes | — | PDF, TXT, PNG, or JPEG |
| `redaction_style` | No | `"black_bar"` | `"black_bar"`, `"placeholder"`, or `"partial"` |
| `webhook_url` | No | — | HTTPS completion callback |
| `language` | No | `"en"` | `en`, `zh`, `es`, `hi`, `ar` |

Response: `{"id": "uuid", "status": "queued"}`
Errors: 400 (bad format/params), 401 (bad key), 402 (PII redaction not on plan — Enterprise — or credits do not cover the job), 413 (over 2,000 pages / 500 MB), 429 (rate or pages in flight; `Retry-After`)

**GET /v1/pii/{job_id}** — Auth: `X-API-Key`. Poll: 5-10s intervals.
Statuses: `queued` -> `processing` -> `completed` | `failed`

Completed: `{id, status, progress_percent, redacted_file_url, report: {page_count, processing_time_ms, pii_detected: {TYPE: {count, pages, confidence_avg}}, total_redactions, redaction_policy, confidence_threshold_used}, error: null}`

Failed: `{id, status: "failed", error: {code: "DOCUMENT_CORRUPTED", message: "..."}}`

## Detection Report

| Field | Description |
|-------|-------------|
| `page_count` | Pages processed |
| `processing_time_ms` | Processing time in ms |
| `pii_detected` | Detections by type: `{count, pages, confidence_avg}` |
| `total_redactions` | Total redactions applied |
| `redaction_policy` | Style used |
| `confidence_threshold_used` | Threshold (default 0.85) |

## Webhooks

Add `webhook_url` to POST /v1/pii/redact. Every delivery is signed: `X-DeepRead-Signature: t=<unix seconds>,v1=<hex>`, HMAC-SHA256 over `"<t>.<raw body>"` keyed by your account's secret (`GET /dashboard/v1/webhooks/secret`; rotate with `POST /dashboard/v1/webhooks/secret/rotate`). Verify over the exact bytes, compare in constant time, reject `t` older than 5 minutes. `GET /v1/pii/{id}` stays the canonical result. HTTPS only. Return 2xx. Design for idempotency.

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

Completed payload: `{job_id, status: "completed", redacted_file_url, report: {page_count, processing_time_ms, pii_detected, total_redactions}}`
Failed payload: `{job_id, status: "failed", error: {code, message}}`

## Error Codes

`INVALID_REQUEST` | `UNSUPPORTED_FORMAT` | `DOCUMENT_CORRUPTED` | `PASSWORD_PROTECTED` | `EMPTY_DOCUMENT` | `FILE_TOO_LARGE` | `RATE_LIMITED` | `INTERNAL_ERROR`

## Rate Limits & Plans

PII redaction is an **Enterprise** feature; other plans receive `402` with the plan named.

| Plan | Pages | Price |
|------|-------|-------|
| Free | 2,000 a month (resets on your signup day); no pii redaction | $0 (no credit card) |
| Standard | No page limits; no pii redaction | Prepaid credits from $15 per 1,000 pages (Extract $15, Deep Extract $35) |
| Enterprise | Custom — includes form fill, PII redaction, searchable PDF, retention, incognito, BYOK | Custom |

Submits per minute: 10 Free, 100 Standard, 500 Enterprise (`429` + `Retry-After` past the limit). Pages in flight (queued + processing jobs; a form-fill job counts as one page): 16 / 200 / 500. Hard maximum for everyone: 2,000 pages or 500 MB (`413`).

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Used`, `X-RateLimit-Reset`

## Code Examples

### Python
```python
import requests, time
API_KEY, BASE = "sk_live_YOUR_KEY", "https://api.deepread.tech"
with open("contract.pdf","rb") as f:
    job_id = requests.post(f"{BASE}/v1/pii/redact", headers={"X-API-Key":API_KEY},
        files={"file":f}, data={"redaction_style":"black_bar"}).json()["id"]
delay = 5
while True:
    time.sleep(delay)
    r = requests.get(f"{BASE}/v1/pii/{job_id}", headers={"X-API-Key":API_KEY}).json()
    if r["status"] in ("completed","failed"): break
    delay = min(delay*1.5, 30)
if r["status"] == "completed":
    print(f"Download: {r['redacted_file_url']}")
    print(f"Redactions: {r['report']['total_redactions']}")
```

### JavaScript
```javascript
import fs from "fs";
const form = new FormData();
form.append("file", fs.createReadStream("contract.pdf"));
form.append("redaction_style", "black_bar");
const {id:jobId} = await fetch("https://api.deepread.tech/v1/pii/redact",
  {method:"POST", headers:{"X-API-Key":"sk_live_YOUR_KEY"}, body:form}).then(r=>r.json());
let delay=5000, result;
do {
  await new Promise(r=>setTimeout(r,delay));
  result = await fetch(`https://api.deepread.tech/v1/pii/${jobId}`,{headers:{"X-API-Key":"sk_live_YOUR_KEY"}}).then(r=>r.json());
  delay = Math.min(delay*1.5,30000);
} while(!["completed","failed"].includes(result.status));
```

### cURL
```bash
curl -X POST https://api.deepread.tech/v1/pii/redact -H "X-API-Key: YOUR_KEY" \
  -F "file=@contract.pdf" -F "redaction_style=black_bar"
curl https://api.deepread.tech/v1/pii/JOB_ID -H "X-API-Key: YOUR_KEY"
```

## Troubleshooting

- **400 "Unsupported file format"** — PDF, TXT, PNG, JPEG only
- **400 "Webhook URL must use HTTPS"** — Change `http://` to `https://`
- **400 "Synthetic redaction style is not available"** — Use `black_bar`, `placeholder`, or `partial`
- **402 not on plan** — PII redaction is an Enterprise feature; upgrade the plan
- **429 with `Retry-After`** — Too many submits this minute or too many pages in flight; wait and retry
- **"DOCUMENT_CORRUPTED"** — File may be damaged. Try re-uploading

**Quick ref:** No key -> device flow (see deepread-setup) | Redact -> POST /v1/pii/redact with `file` | Results -> GET /v1/pii/{id} | Download -> `redacted_file_url` | Styles -> black_bar/placeholder/partial | Non-English -> `language` param
