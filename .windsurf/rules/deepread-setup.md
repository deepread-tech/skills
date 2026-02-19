# Setup DeepRead

AI-native OCR API — extracts text and structured data from PDFs/images with 97%+ accuracy.

**API:** `https://api.deepread.tech` | **Dashboard:** `https://www.deepread.tech`

## Step 1: Get an API Key (Device Authorization Flow)

The agent obtains the key — no copy/paste needed.

> **CRITICAL — run the entire device flow as ONE terminal command block.** Shell variables do not persist between separate executions. If you split this, the `device_code` is lost.

Complete flow in a single script:

```bash
# Get device code
dr_response=$(curl -s -X POST https://api.deepread.tech/v1/agent/device/code \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "Windsurf"}')
dr_device_code=$(echo "$dr_response" | jq -r '.device_code')
dr_user_code=$(echo "$dr_response" | jq -r '.user_code')
dr_uri=$(echo "$dr_response" | jq -r '.verification_uri_complete')
dr_interval=$(echo "$dr_response" | jq -r '.interval')

# Validate response
if [ "$dr_device_code" = "null" ] || [ -z "$dr_device_code" ]; then
  echo "ERROR: API did not return a device_code. Response: $dr_response"
  exit 1
fi

echo "Opening browser: $dr_uri"
open "$dr_uri" 2>/dev/null || xdg-open "$dr_uri" 2>/dev/null || echo "Open manually: $dr_uri"
echo "Waiting for approval of code: $dr_user_code"

# Poll until approved (dr_ prefix avoids variable name conflicts)
dr_api_key=""
for dr_i in $(seq 1 72); do
  sleep "$dr_interval"
  dr_result=$(curl -s -X POST https://api.deepread.tech/v1/agent/device/token \
    -H "Content-Type: application/json" \
    -d "{\"device_code\": \"$dr_device_code\"}")
  dr_api_key=$(echo "$dr_result" | jq -r '.api_key')
  dr_error=$(echo "$dr_result" | jq -r '.error')
  dr_prefix=$(echo "$dr_result" | jq -r '.key_prefix')

  if [ "$dr_api_key" != "null" ] && [ -n "$dr_api_key" ]; then
    echo "SUCCESS key_prefix=$dr_prefix"
    echo "DEEPREAD_API_KEY=$dr_api_key"
    break
  elif [ "$dr_error" = "access_denied" ]; then echo "DENIED"; break
  elif [ "$dr_error" = "expired_token" ]; then echo "EXPIRED"; break
  else echo "attempt=$dr_i pending..."; fi
done
```

Never show the `device_code`. Only show `user_code` and the browser URL. Use `dr_` prefix for all variables to avoid shell built-in conflicts.

| `error` | `api_key` | Action |
|---------|-----------|--------|
| `"authorization_pending"` | `null` | Wait, poll again |
| `null` | `"sk_live_..."` | Save key, stop polling |
| `"access_denied"` | `null` | Stop, inform user |
| `"expired_token"` | `null` | Start over |

**Store the key safely** — returned exactly once, then cleared from server:
```bash
printf "\nDEEPREAD_API_KEY=%s\n" "$dr_api_key" >> .env
```
Never use `echo` — if `.env` doesn't end with a newline, the key merges with the previous line.

## Step 2: Send Your First Document

> **Split submit and poll into separate steps.** Submit first, confirm the job ID, then check results separately.

**Submit:**
```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)
curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: $DR_API_KEY" \
  -F "file=@document.pdf"
# → {"id": "550e8400-...", "status": "queued"}
```

**Check results** (after 2-3 minutes — use python3, not jq, for large responses):
```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)
dr_job_id="THE_JOB_ID"

# Guard: bail if job ID is empty
if [ -z "$dr_job_id" ] || [ "$dr_job_id" = "null" ]; then
  echo "ERROR: No job ID — submit may have failed."
  exit 1
fi

curl -s "https://api.deepread.tech/v1/jobs/$dr_job_id" -H "X-API-Key: $DR_API_KEY" > /tmp/deepread_result.json
python3 -c "
import json
with open('/tmp/deepread_result.json') as f:
    data = json.load(f)
print('Status:', data.get('status'))
if data.get('status') == 'completed':
    print(json.dumps({'preview_url': data.get('preview_url'), 'page_count': len(data.get('result',{}).get('pages',[])) if data.get('result') else 0, 'text_preview': (data.get('result',{}).get('text','') or '')[:500]}, indent=2))
elif data.get('status') == 'failed':
    print('Error:', data.get('error'))
"
```
Supports: PDF, PNG, JPG, JPEG. Max 15 MB (free) / 50 MB (paid).

## Step 3: Extract Structured Data

Pass a JSON Schema — field descriptions guide the AI:

**Submit with schema:**
```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)
curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: $DR_API_KEY" \
  -F "file=@invoice.pdf" \
  -F 'schema={"type":"object","properties":{"vendor":{"type":"string","description":"Company name on invoice"},"total":{"type":"number","description":"Total amount due"},"due_date":{"type":"string","description":"Payment due date"}}}'
```

**Fetch structured results** (same pattern — python3 + temp file):
```bash
DR_API_KEY=$(grep ^DEEPREAD_API_KEY .env | cut -d= -f2)
curl -s "https://api.deepread.tech/v1/jobs/JOB_ID" -H "X-API-Key: $DR_API_KEY" > /tmp/deepread_structured_result.json
python3 -c "
import json
with open('/tmp/deepread_structured_result.json') as f:
    data = json.load(f)
print('Status:', data.get('status'))
if data.get('status') == 'completed':
    fields = data.get('result',{}).get('data',{})
    if fields: print(json.dumps(fields, indent=2))
    print('Preview:', data.get('preview_url','N/A'))
"
```

Each field includes quality metadata:
```json
{
  "vendor": {"value": "Acme Inc", "hil_flag": false, "found_on_page": 1},
  "due_date": {"value": "2025-03-15", "hil_flag": true, "reason": "Multiple dates found"}
}
```
`hil_flag: false` = auto-accept. `hil_flag: true` = needs human review.

## Step 4: Blueprints (20-30% Better Accuracy)

Optimized schemas built from your sample documents + ground truth data.

1. Go to `https://www.deepread.tech/dashboard/optimizer`
2. Upload 4+ sample docs + ground truth JSON → DeepRead optimizes automatically
3. Use the blueprint:
```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: sk_live_YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F "blueprint_id=YOUR_BLUEPRINT_ID"
```
Use `schema` OR `blueprint_id`, not both.

## Plans

| Plan | Pages/month | Max file | Per-doc limit | Price |
|------|-------------|----------|---------------|-------|
| Free | 2,000 | 15 MB | 50 pages | $0 |
| Pro | 50,000 | 50 MB | Unlimited | $99/mo |
| Scale | 1,000,000 | 50 MB | Unlimited | Custom |

## Quick Reference

- No key → device flow (Step 1)
- First request → Step 2
- Structured data → Step 3 (write good field descriptions)
- Better accuracy → Step 4 (blueprints)
- Full API → see `deepread-api` rule
