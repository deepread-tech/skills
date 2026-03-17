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
Errors: 400 (bad format/params), 401 (bad key), 413 (too large), 429 (quota/rate)

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

Add `webhook_url` to POST /v1/pii/redact. Always re-fetch via `GET /v1/pii/{id}` — webhooks are unauthenticated. HTTPS only. Return 2xx. Design for idempotency.

Completed payload: `{job_id, status: "completed", redacted_file_url, report: {page_count, processing_time_ms, pii_detected, total_redactions}}`
Failed payload: `{job_id, status: "failed", error: {code, message}}`

## Error Codes

`INVALID_REQUEST` | `UNSUPPORTED_FORMAT` | `DOCUMENT_CORRUPTED` | `PASSWORD_PROTECTED` | `EMPTY_DOCUMENT` | `FILE_TOO_LARGE` | `RATE_LIMITED` | `INTERNAL_ERROR`

## Rate Limits & Plans

| Plan | Pages/month | Price |
|------|-------------|-------|
| Free | 2,000 | $0 (no credit card) |
| Pro | 50,000 | $99/mo |
| Scale | Custom | Custom pricing |

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
- **429 quota exceeded** — Upgrade to PRO or wait for next billing cycle
- **"DOCUMENT_CORRUPTED"** — File may be damaged. Try re-uploading

**Quick ref:** No key -> device flow (see deepread-setup) | Redact -> POST /v1/pii/redact with `file` | Results -> GET /v1/pii/{id} | Download -> `redacted_file_url` | Styles -> black_bar/placeholder/partial | Non-English -> `language` param
