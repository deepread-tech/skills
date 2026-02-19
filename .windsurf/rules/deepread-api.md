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
| `file` | Yes | — | PDF, PNG, JPG, JPEG |
| `pipeline` | No | `"standard"` | `"standard"` or `"searchable"` |
| `schema` | No | — | JSON Schema string for structured extraction |
| `blueprint_id` | No | — | UUID (mutually exclusive with schema) |
| `include_images` | No | `"true"` | Preview images + page data |
| `include_pages` | No | `"false"` | Per-page breakdown |
| `webhook_url` | No | — | HTTPS completion callback |
| `version` | No | — | Pipeline version pin |

Response: `{"id": "uuid", "status": "queued"}`
Errors: 400 (bad schema/file), 401 (bad key), 413 (too large), 429 (quota/rate)

**GET /v1/jobs/{job_id}** — Auth: `X-API-Key`. Poll: wait 5s, then 5-10s backoff (max 5 min).
Statuses: `queued` → `processing` → `completed` | `failed`

Completed: `{status, result: {text, text_preview, text_url (>1MB), data: {field: {value, hil_flag, found_on_page, reason?}}, pages: [{page_number, text, hil_flag, data}]}, metadata: {page_count, pipeline, review_percentage}, preview_url}`

**GET /v1/preview/{token}** — Auth: None. Public shareable preview.
**GET /v1/pipelines** — Auth: None. `standard` (~2-3 min) | `searchable` PDF (~3-4 min)

## Blueprints & Optimizer

**GET /v1/blueprints/** — List blueprints (Auth: API key)
**GET /v1/blueprints/{id}** — Details with versions and accuracy metrics

**POST /v1/optimize** — Auth: API key. Fields: `name`, `document_type`, `training_documents` (min 2), `ground_truth_data`, `target_accuracy`, `max_iterations`, `max_cost_usd`. `initial_schema` optional (auto-generated). Response: `{job_id, blueprint_id, status}`

**POST /v1/optimize/resume** — Resume failed optimization
**GET /v1/blueprints/jobs/{id}** — Progress: `{status, iteration, current_accuracy, total_cost}`
**GET /v1/blueprints/jobs/{id}/schema** — Optimized schema after completion

## Webhooks

Add `webhook_url` to POST /v1/process. Always re-fetch via `GET /v1/jobs/{id}` — webhooks are unauthenticated. Return 2xx. Design for idempotency.

## Rate Limits & Plans

| Plan | Pages/month | Max file | Per-doc | Rate |
|------|-------------|----------|---------|------|
| Free | 2,000 | 15 MB | 50 pages | 10 req/min |
| Pro ($99/mo) | 50,000 | 50 MB | Unlimited | 100 req/min |
| Scale | 1,000,000 | 50 MB | Unlimited | 500 req/min |

Response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Used`, `X-RateLimit-Reset`

## Errors — `{"detail": "message"}`

400 (bad schema/file/both schema+blueprint) | 401 (bad key) | 404 (not found) | 413 (file too large) | 429 (rate/quota) | 500 (server)

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

**Quick ref:** No key → device flow (see deepread-setup) | Submit → POST /v1/process | Results → GET /v1/jobs/{id} | Structured → `schema` | Better accuracy → `blueprint_id` | Share → `preview_url` | HIL → filter by `hil_flag: true`
