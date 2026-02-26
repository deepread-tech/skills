---
description: "DeepRead Form Fill API. AI-powered PDF form filling — upload any PDF form + JSON data, get back a completed PDF. Endpoints, auth, request/response formats, and code examples."
---

# DeepRead Form Fill API Reference

**Base URL:** `https://api.deepread.tech` | **Auth:** `X-API-Key` header

## What It Does

Upload any PDF form + your data as JSON. AI detects fields visually, maps your data semantically, fills the form, and returns a completed PDF with quality report. Works with any PDF — scanned forms, government PDFs, custom templates. No AcroForm fields required.

## POST /v1/form-fill — Submit a Form for Filling

**Auth:** `X-API-Key`. Content-Type: `multipart/form-data`

| Param | Req | Default | Description |
|-------|-----|---------|-------------|
| `file` | Yes | — | PDF form to fill |
| `form_fields` | Yes | — | JSON string: `{"field_name": "value"}` |
| `webhook_url` | No | — | HTTPS completion callback |
| `idempotency_key` | No | — | Prevent duplicate submissions |
| `url_expires_in` | No | `604800` | Signed URL expiry in seconds (min: 3600, max: 604800 = 7 days) |

Response: `{"id": "uuid", "status": "queued"}`
Errors: 400 (bad JSON/file), 401 (bad key), 429 (quota/rate)

**GET /v1/form-fill/{job_id}** — Auth: `X-API-Key`. Rate limit: 20 req/60s. Poll: 5-10s intervals.
Statuses: `queued` -> `processing` -> `completed` | `failed`

Completed: `{status, file_name, filled_form_url, fields_detected, fields_filled, fields_verified, fields_hil_flagged, duration_seconds, report: {summary, fields: [{field_index, label, field_type, page, value, hil_flag, verified, reason?}], mappings: [{user_key, field_index, value_to_fill, confidence}], unmapped_user_keys, adjustments_made, qa_feedback, errors}}`

Failed: `{status: "failed", error_message: "..."}`

## Report Metrics

| Metric | Meaning |
|--------|---------|
| `fields_detected` | Total form fields AI found on PDF |
| `fields_filled` | Fields where your data was placed |
| `fields_verified` | Fields that passed visual QA |
| `fields_hil_flagged` | Fields needing human review |

Typical: 90-95% verified, 2-5% flagged. Each flagged field has a `reason`.

## Webhooks

Add `webhook_url` to POST /v1/form-fill. Always re-fetch via `GET /v1/form-fill/{id}` — webhooks are unauthenticated. Return 2xx. Design for idempotency.

Completed payload: `{job_id, status: "completed", result: {filled_form_url, fields_detected, fields_filled, fields_verified, fields_hil_flagged, report}}`
Failed payload: `{job_id, status: "failed", error, errors}`

## Idempotency

Send `idempotency_key` to prevent duplicates. Same key returns same job ID.

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
import requests, time, json
API_KEY, BASE = "sk_live_YOUR_KEY", "https://api.deepread.tech"
form_fields = {"full_name": "Jane Doe", "date_of_birth": "03/15/1990", "address": "123 Main St"}
with open("application.pdf","rb") as f:
    job_id = requests.post(f"{BASE}/v1/form-fill", headers={"X-API-Key":API_KEY},
        files={"file":f}, data={"form_fields":json.dumps(form_fields)}).json()["id"]
delay = 5
while True:
    time.sleep(delay)
    r = requests.get(f"{BASE}/v1/form-fill/{job_id}", headers={"X-API-Key":API_KEY}).json()
    if r["status"] in ("completed","failed"): break
    delay = min(delay*1.5, 30)
if r["status"] == "completed":
    print(f"Download: {r['filled_form_url']}")
    print(f"Fields: {r['fields_filled']}/{r['fields_detected']} filled, {r['fields_hil_flagged']} need review")
```

### JavaScript
```javascript
import fs from "fs";
const form = new FormData();
form.append("file", fs.createReadStream("application.pdf"));
form.append("form_fields", JSON.stringify({full_name:"Jane Doe",date_of_birth:"03/15/1990"}));
const {id:jobId} = await fetch("https://api.deepread.tech/v1/form-fill",
  {method:"POST", headers:{"X-API-Key":"sk_live_YOUR_KEY"}, body:form}).then(r=>r.json());
let delay=5000, result;
do {
  await new Promise(r=>setTimeout(r,delay));
  result = await fetch(`https://api.deepread.tech/v1/form-fill/${jobId}`,{headers:{"X-API-Key":"sk_live_YOUR_KEY"}}).then(r=>r.json());
  delay = Math.min(delay*1.5,30000);
} while(!["completed","failed"].includes(result.status));
```

### cURL
```bash
curl -X POST https://api.deepread.tech/v1/form-fill -H "X-API-Key: YOUR_KEY" \
  -F "file=@application.pdf" -F 'form_fields={"full_name":"Jane Doe","date_of_birth":"03/15/1990"}'
curl https://api.deepread.tech/v1/form-fill/JOB_ID -H "X-API-Key: YOUR_KEY"
```

## Troubleshooting

- **400 "Only PDF files are supported"** — PDF only, other formats not yet supported
- **400 "Invalid JSON in form_fields"** — Must be valid JSON object, not array or string
- **429 quota exceeded** — Upgrade to PRO or wait for next billing cycle
- **"Vision model timeout"** — Complex/large form. Try splitting into sections
- **Fields not mapped** — Use descriptive key names: `"applicant_full_name"` not `"field1"`
- **Fields flagged** — Expected for 2-5%. Check `report.fields` for `reason`

**Quick ref:** No key -> device flow (see deepread-setup) | Fill form -> POST /v1/form-fill with `file` + `form_fields` | Results -> GET /v1/form-fill/{id} | Download -> `filled_form_url` | Duplicates -> `idempotency_key` | Review -> filter by `hil_flag: true`
