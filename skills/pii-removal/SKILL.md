---
name: pii-removal
description: PII removal API. Upload documents, automatically detect and redact personal information (SSN, credit cards, names, etc.), download redacted files. Endpoints, auth, request/response formats, and code examples.
allowed-tools: Bash, Read, Write
user-invocable: true
---

# DeepRead PII Removal

You are helping a developer redact PII from documents using DeepRead's PII removal API. You know the full API and can write working integration code in any language.

**Base URL:** `https://api.deepread.tech`
**Auth:** `X-API-Key` header with key from `https://www.deepread.tech/dashboard` or via the device authorization flow (use `/setup`)

---

## What PII Removal Does

The developer provides:
1. A document (PDF, text file, or image)
2. Optional configuration (redaction style, language)

DeepRead returns:
- A redacted document with all PII removed
- A detection report showing what was found, where, and confidence scores

**14 PII types detected automatically:** SSN, credit cards, emails, phone numbers, names, addresses, dates of birth, passport numbers, driver's license numbers, bank accounts, IP addresses, medical record numbers, tax IDs, and biometric identifiers.

---

## Prerequisites

You need a `DEEPREAD_API_KEY`. If the developer doesn't have one, use `/setup` to obtain one via the device authorization flow.

---

## API Endpoints

### POST /v1/pii/redact — Submit a Document for Redaction

Uploads a document for async PII detection and redaction. Returns immediately with a job ID.

**Auth:** `X-API-Key: YOUR_KEY`
**Content-Type:** `multipart/form-data`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `file` | File | Yes | — | PDF, TXT, PNG, or JPEG |
| `redaction_style` | string | No | `"black_bar"` | `"black_bar"`, `"placeholder"`, or `"partial"` |
| `webhook_url` | string | No | — | HTTPS URL to receive results when done |
| `language` | string | No | `"en"` | Document language: `en`, `zh`, `es`, `hi`, `ar` |

**Redaction styles:**
| Style | What it does | Example |
|-------|-------------|---------|
| `black_bar` | Black rectangles over PII | `███████████` |
| `placeholder` | Replace with type labels | `[NAME]`, `[SSN]`, `[EMAIL]` |
| `partial` | Partial reveal | `***-**-6789`, `****-****-****-0366` |

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

**Errors:**
| Status | Meaning |
|--------|---------|
| 400 | Unsupported file format, empty file, invalid parameters, non-HTTPS webhook |
| 401 | Invalid or missing API key |
| 413 | File exceeds size limit |
| 429 | Monthly page quota exceeded or rate limit hit |

---

### GET /v1/pii/{job_id} — Get Job Status & Results

Poll until `status` is `completed` or `failed`. Recommended: poll every 5-10 seconds.

**Auth:** `X-API-Key: YOUR_KEY`

**Response (completed):**
```json
{
  "id": "550e8400-...",
  "status": "completed",
  "progress_percent": 100,
  "redacted_file_url": "https://storage.deepread.tech/pii/.../redacted.pdf",
  "report": {
    "id": "550e8400-...",
    "page_count": 3,
    "processing_time_ms": 4200,
    "pii_detected": {
      "SSN": {
        "count": 2,
        "pages": [1, 2],
        "confidence_avg": 0.97
      },
      "EMAIL": {
        "count": 3,
        "pages": [1],
        "confidence_avg": 0.99
      },
      "NAME": {
        "count": 5,
        "pages": [1, 2, 3],
        "confidence_avg": 0.92
      }
    },
    "total_redactions": 10,
    "redaction_policy": "black_bar",
    "confidence_threshold_used": 0.85
  },
  "error": null
}
```

**Response (failed):**
```json
{
  "id": "550e8400-...",
  "status": "failed",
  "progress_percent": 0,
  "redacted_file_url": null,
  "report": null,
  "error": {
    "code": "DOCUMENT_CORRUPTED",
    "message": "Failed to parse the uploaded document"
  }
}
```

**Statuses:** `queued` -> `processing` -> `completed` or `failed`

---

## Detection Report

The `report` object in a completed response contains:

| Field | Description |
|-------|-------------|
| `page_count` | Number of pages processed |
| `processing_time_ms` | Processing time in milliseconds |
| `pii_detected` | Detections grouped by PII type |
| `total_redactions` | Total number of redactions applied |
| `redaction_policy` | Redaction style used |
| `confidence_threshold_used` | Confidence threshold (default 0.85) |

Each PII type in `pii_detected` includes:
- `count` — number of instances found
- `pages` — which pages they appear on
- `confidence_avg` — average confidence score (0-1)

---

## PII Types Detected

| Type | Examples |
|------|---------|
| `SSN` | Social Security Numbers (123-45-6789) |
| `CREDIT_CARD` | Credit/debit card numbers |
| `EMAIL` | Email addresses |
| `PHONE` | Phone numbers |
| `NAME` | Personal names |
| `ADDRESS` | Physical/mailing addresses |
| `DATE_OF_BIRTH` | Dates of birth |
| `PASSPORT` | Passport numbers |
| `DRIVER_LICENSE` | Driver's license numbers |
| `BANK_ACCOUNT` | Bank account/routing numbers |
| `IP_ADDRESS` | IP addresses |
| `MEDICAL_RECORD` | Medical record numbers (MRN) |
| `TAX_ID` | Tax identification numbers (EIN, ITIN) |
| `BIOMETRIC` | Biometric identifiers |

---

## Webhooks

Pass `webhook_url` when submitting a document to get notified on completion.

**Completed payload:**
```json
{
  "job_id": "550e8400-...",
  "status": "completed",
  "redacted_file_url": "https://storage.deepread.tech/pii/.../redacted.pdf",
  "report": {
    "page_count": 3,
    "processing_time_ms": 4200,
    "pii_detected": { ... },
    "total_redactions": 10
  }
}
```

**Failed payload:**
```json
{
  "job_id": "550e8400-...",
  "status": "failed",
  "error": {
    "code": "DOCUMENT_CORRUPTED",
    "message": "Failed to parse the uploaded document"
  }
}
```

**Important:**
- Webhooks are **NOT authenticated** — always fetch the canonical result via `GET /v1/pii/{job_id}` with your API key
- Must be HTTPS (HTTP and private IPs are rejected)
- Return 2xx to confirm delivery
- Make your endpoint idempotent (may receive duplicates)

---

## Supported Languages

| Code | Language |
|------|----------|
| `en` | English (default) |
| `zh` | Chinese |
| `es` | Spanish |
| `hi` | Hindi |
| `ar` | Arabic |

---

## Code Examples

### Python

```python
import requests
import time

API_KEY = "sk_live_YOUR_KEY"
BASE = "https://api.deepread.tech"

# Submit document for PII redaction
with open("contract.pdf", "rb") as f:
    resp = requests.post(
        f"{BASE}/v1/pii/redact",
        headers={"X-API-Key": API_KEY},
        files={"file": f},
        data={
            "redaction_style": "black_bar",
            "language": "en",
        }
    )
job_id = resp.json()["id"]

# Poll for results
delay = 5
while True:
    time.sleep(delay)
    result = requests.get(
        f"{BASE}/v1/pii/{job_id}",
        headers={"X-API-Key": API_KEY}
    ).json()

    if result["status"] in ("completed", "failed"):
        break
    delay = min(delay * 1.5, 30)

# Use results
if result["status"] == "completed":
    print(f"Download: {result['redacted_file_url']}")
    report = result["report"]
    print(f"Pages: {report['page_count']}")
    print(f"Redactions: {report['total_redactions']}")
    for pii_type, info in report["pii_detected"].items():
        print(f"  {pii_type}: {info['count']} found (avg confidence: {info['confidence_avg']:.0%})")
else:
    error = result.get("error", {})
    print(f"Failed: {error.get('message', 'Unknown error')}")
```

### JavaScript / Node.js

```javascript
import fs from "fs";

const API_KEY = "sk_live_YOUR_KEY";
const BASE = "https://api.deepread.tech";

// Submit document for PII redaction
const form = new FormData();
form.append("file", fs.createReadStream("contract.pdf"));
form.append("redaction_style", "black_bar");

const { id: jobId } = await fetch(`${BASE}/v1/pii/redact`, {
  method: "POST",
  headers: { "X-API-Key": API_KEY },
  body: form
}).then(r => r.json());

// Poll for results
let delay = 5000;
let result;
do {
  await new Promise(r => setTimeout(r, delay));
  result = await fetch(`${BASE}/v1/pii/${jobId}`, {
    headers: { "X-API-Key": API_KEY }
  }).then(r => r.json());
  delay = Math.min(delay * 1.5, 30000);
} while (!["completed", "failed"].includes(result.status));

if (result.status === "completed") {
  console.log("Download:", result.redacted_file_url);
  console.log("Redactions:", result.report.total_redactions);
  for (const [type, info] of Object.entries(result.report.pii_detected)) {
    console.log(`  ${type}: ${info.count} found`);
  }
} else {
  console.log("Failed:", result.error?.message);
}
```

### cURL

```bash
# Submit document for PII redaction
curl -X POST https://api.deepread.tech/v1/pii/redact \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@contract.pdf" \
  -F "redaction_style=black_bar"

# With placeholder style and webhook
curl -X POST https://api.deepread.tech/v1/pii/redact \
  -H "X-API-Key: YOUR_KEY" \
  -F "file=@medical_record.pdf" \
  -F "redaction_style=placeholder" \
  -F "webhook_url=https://your-app.com/webhooks/pii"

# Get results (use job_id from response)
curl https://api.deepread.tech/v1/pii/JOB_ID \
  -H "X-API-Key: YOUR_KEY"
```

---

## Error Codes

| Code | Meaning |
|------|---------|
| `INVALID_REQUEST` | Bad parameters, invalid job ID |
| `UNSUPPORTED_FORMAT` | File type not supported (use PDF, TXT, PNG, JPEG) |
| `DOCUMENT_CORRUPTED` | Cannot parse the document |
| `PASSWORD_PROTECTED` | PDF is password-protected |
| `EMPTY_DOCUMENT` | Uploaded file is empty |
| `FILE_TOO_LARGE` | File exceeds size limit |
| `RATE_LIMITED` | Too many requests |
| `INTERNAL_ERROR` | Server error — retry later |

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| 400 "Unsupported file format" | Use PDF, TXT, PNG, or JPEG |
| 400 "Uploaded file is empty" | File has zero bytes |
| 400 "Webhook URL must use HTTPS" | Change `http://` to `https://` |
| 400 "Webhook URL cannot use private IP" | Use a public URL, not `192.168.x.x` or `localhost` |
| 400 "Synthetic redaction style is not available" | Use `black_bar`, `placeholder`, or `partial` |
| 429 "Rate limit exceeded" | Slow down requests or upgrade plan |
| Status "failed" with "DOCUMENT_CORRUPTED" | File may be damaged. Try re-uploading or converting to PDF |

---

## Rate Limits

**Plans:**
| Plan | Pages/month | Price |
|------|-------------|-------|
| Free | 2,000 | $0 (no credit card) |
| Pro | 50,000 | $99/mo |
| Scale | Custom | Custom |

---

## Help the Developer

- **No API key yet** -> use `/setup` for the device authorization flow
- **Redact a document** -> POST /v1/pii/redact with `file`, show code in their language
- **Check results** -> GET /v1/pii/{job_id}, explain the detection report
- **Download redacted doc** -> use `redacted_file_url` from completed response
- **Different redaction styles** -> explain black_bar vs placeholder vs partial
- **Non-English documents** -> use `language` parameter (zh, es, hi, ar)
- **Real-time updates** -> set up `webhook_url`, build receiver endpoint
- **Hitting errors** -> check API key, plan limits, file format
