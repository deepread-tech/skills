# Setup DeepRead

AI-native OCR API — extracts text and structured data from PDFs/images with 97%+ accuracy.

**API:** `https://api.deepread.tech` | **Dashboard:** `https://www.deepread.tech`

## Step 1: Get an API Key (Device Authorization Flow)

The agent obtains the key — no copy/paste needed.

**1a. Request a device code** (one call, save all fields):
```bash
response=$(curl -s -X POST https://api.deepread.tech/v1/agent/device/code \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "YOUR_AGENT_NAME"}')
device_code=$(echo "$response" | jq -r '.device_code')
verification_uri_complete=$(echo "$response" | jq -r '.verification_uri_complete')
interval=$(echo "$response" | jq -r '.interval')
```
Response fields: `device_code`, `user_code`, `verification_uri_complete`, `expires_in: 900`, `interval: 5`

**1b. Open the browser** (use URL from 1a — never call the API again):
```bash
open "$verification_uri_complete"      # macOS
xdg-open "$verification_uri_complete"  # Linux
```
If headless, show the user: `https://www.deepread.tech/activate?code=XXXX-XXXX`
Never show the `device_code`. Already logged-in users are auto-validated. New users sign up then return to approve.

**1c. Poll for the key** (every `interval` seconds):
```bash
curl -s -X POST https://api.deepread.tech/v1/agent/device/token \
  -H "Content-Type: application/json" \
  -d '{"device_code": "a7f3c9d2..."}'
```

| `error` | `api_key` | Action |
|---------|-----------|--------|
| `"authorization_pending"` | `null` | Wait, poll again |
| `null` | `"sk_live_..."` | Save key, stop polling |
| `"access_denied"` | `null` | Stop, inform user |
| `"expired_token"` | `null` | Start over from 1a |

**1d. Store the key** — returned exactly once, then cleared from server.

## Step 2: Send Your First Document

```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: sk_live_YOUR_KEY" \
  -F "file=@document.pdf"
# → {"id": "550e8400-...", "status": "queued"}

# Poll for results (wait 5s, then every 5-10s):
curl https://api.deepread.tech/v1/jobs/550e8400-... \
  -H "X-API-Key: sk_live_YOUR_KEY"
```
Supports: PDF, PNG, JPG, JPEG. Max 15 MB (free) / 50 MB (paid).

## Step 3: Extract Structured Data

Pass a JSON Schema — field descriptions guide the AI:
```bash
curl -X POST https://api.deepread.tech/v1/process \
  -H "X-API-Key: sk_live_YOUR_KEY" \
  -F "file=@invoice.pdf" \
  -F 'schema={"type":"object","properties":{"vendor":{"type":"string","description":"Company name on invoice"},"total":{"type":"number","description":"Total amount due"},"due_date":{"type":"string","description":"Payment due date"}}}'
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
