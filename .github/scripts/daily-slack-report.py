#!/usr/bin/env python3
"""
DeepRead daily Slack report (cloud / GitHub Actions edition).

Pulls live ClawHub stats for every DeepRead skill from the PUBLIC registry API
(no login needed), compares to the previous run (state persisted via Actions
cache) for day-over-day deltas, and posts a fresh DeepRead highlight + the
stats table to a Slack incoming webhook.

Config via env:
  SLACK_WEBHOOK_URL       (required) Slack incoming webhook
  DEEPREAD_STATE_DIR      (optional) where to read/write the snapshot. default: .deepread-state
  DEEPREAD_REPORT_UNTIL   (optional) YYYY-MM-DD; if today is past this, skip posting (campaign window)
No secrets live in this file — the webhook is injected from a GitHub secret at runtime.
"""
import json, os, sys, urllib.request, datetime

REGISTRY = "https://clawhub.ai/api/v1/skills/{slug}"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

STATE_DIR = os.environ.get("DEEPREAD_STATE_DIR", ".deepread-state")
SNAP = os.path.join(STATE_DIR, "stats_last.json")

SKILLS = [
    ("deepread-ocr",         "DeepRead OCR"),
    ("deepread-agent-setup", "DeepRead Agent Self Sign Up"),
    ("deepread-pii",         "DeepRead PII Redaction"),
    ("deepread-byok",        "DeepRead BYOK"),
    ("deepread-form-fill",   "DeepRead Form Fill"),
    ("deepread-invoice",     "DeepRead Invoice"),
    ("deepread-insurance",   "DeepRead Insurance"),
    ("deepread-legal",       "DeepRead Legal"),
    ("deepread-medical",     "DeepRead Medical"),
]

# "something new about DeepRead" — rotates daily by date. Each line is true & useful.
HIGHLIGHTS = [
    "DeepRead returns a `needs_review` flag on *every* extracted field — trust the 19 it's sure about, eyeball only the 1 it isn't.",
    "Multi-model consensus: GPT + Gemini + an LLM judge cross-check each other instead of one model guessing alone.",
    "BYOK lets you plug in your own OpenAI/Google/OpenRouter key — page quota disappears and LLM cost goes to your account.",
    "PII redaction covers 14 types and is context-aware — it knows the doctor from the patient, the label from the value.",
    "Form Fill works on *scanned* PDFs with no AcroForm fields — vision AI places text at the right coordinates, then QA-checks itself.",
    "Blueprints optimize a schema from a few labeled samples for a 20-30% accuracy lift on recurring document types.",
    "Free tier is a real 2,000 pages/month, no credit card — anyone can prove it on their own documents before paying.",
    "Pro is $99/mo for 50,000 pages (~$0.002/page). Nanonets starts at $499. That's the whole pitch to an operator.",
    "Shareable preview links (no auth) let a prospect click through their own extracted document — our best demo.",
    "One API does four jobs: OCR, structured JSON extraction, PII redaction, and PDF form-fill. No tool-stitching.",
    "Two accuracy tiers — `fast` (lowest-latency) and `standard` (multi-model consensus) — plus an optional searchable-PDF add-on (`searchable_pdf=true`) on standard.",
    "Webhooks fire on completion so you never poll — always re-fetch the canonical job for an idempotent-safe pipeline.",
    "Schema-free mode: send no schema and still get clean OCR text + auto-detected fields back.",
    "Agent-native: Claude Code / Cursor / Windsurf skills mean a developer's AI writes the DeepRead integration itself.",
    "Per-field `location.page` on every result lets you deep-link a reviewer straight to where a value came from.",
]

def fetch(slug):
    try:
        req = urllib.request.Request(REGISTRY.format(slug=slug), headers={"User-Agent": "deepread-daily/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return (d.get("skill") or {}).get("stats") or {}
    except Exception as e:
        print(f"fetch {slug} failed: {e}")
        return None

def fmt_delta(d):
    if d is None: return ""
    if d > 0:  return f"  (+{d})"
    if d < 0:  return f"  ({d})"
    return "  (–)"

def main():
    webhook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not webhook:
        print("ERROR: SLACK_WEBHOOK_URL not set"); sys.exit(1)

    today = datetime.datetime.now(IST).date()

    until = os.environ.get("DEEPREAD_REPORT_UNTIL", "").strip()
    if until:
        try:
            end = datetime.date.fromisoformat(until)
            if today > end:
                print(f"Campaign window ended on {until}; skipping post. Bump DEEPREAD_REPORT_UNTIL to extend.")
                sys.exit(0)
        except ValueError:
            print(f"WARN: bad DEEPREAD_REPORT_UNTIL '{until}', ignoring")

    os.makedirs(STATE_DIR, exist_ok=True)
    prev = {}
    if os.path.exists(SNAP):
        try: prev = json.load(open(SNAP))
        except Exception: prev = {}

    cur, lines = {}, []
    tot  = {"downloads": 0, "installsCurrent": 0, "stars": 0}
    dtot = {"downloads": 0, "installsCurrent": 0, "stars": 0}

    for slug, name in SKILLS:
        s = fetch(slug)
        if s is None:
            lines.append(f"• {name}: _stats unavailable_"); continue
        cur[slug] = s
        dl, ic, st = s.get("downloads", 0), s.get("installsCurrent", 0), s.get("stars", 0)
        p = prev.get(slug, {})
        d_dl = dl - p["downloads"] if p else None
        for k in tot: tot[k] += s.get(k, 0)
        if p:
            for k in dtot: dtot[k] += s.get(k, 0) - p.get(k, 0)
        lines.append(f"• *{name}*: {dl:,} downloads{fmt_delta(d_dl)} · {ic} installs · {st}★")

    have_prev = bool(prev)
    highlight = HIGHLIGHTS[today.toordinal() % len(HIGHLIGHTS)]
    pretty = today.strftime("%A, %b %d")

    header = f":bar_chart: *DeepRead Daily — {pretty}*"
    tip    = f":bulb: *Something new about DeepRead:* {highlight}"
    if have_prev:
        totline = (f":chart_with_upwards_trend: *Engagement vs yesterday:* "
                   f"*{tot['downloads']:,}* downloads{fmt_delta(dtot['downloads'])} · "
                   f"*{tot['installsCurrent']}* installs{fmt_delta(dtot['installsCurrent'])} · "
                   f"*{tot['stars']}*★{fmt_delta(dtot['stars'])}")
    else:
        totline = (f":chart_with_upwards_trend: *Totals (baseline — deltas start next run):* "
                   f"*{tot['downloads']:,}* downloads · *{tot['installsCurrent']}* installs · *{tot['stars']}*★")

    text = "\n".join([header, "", tip, "", totline, "", "*Per skill:*", *lines, "",
                      "<https://www.deepread.tech/dashboard|Open dashboard>  ·  <https://clawhub.ai/publishers/uday390|ClawHub profile>"])

    body = json.dumps({"text": text}).encode()
    req = urllib.request.Request(webhook, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"posted to Slack: HTTP {r.status}; downloads_total={tot['downloads']} delta={dtot['downloads']}")
    except Exception as e:
        print(f"slack post FAILED: {e}"); sys.exit(1)

    if cur:
        json.dump(cur, open(SNAP, "w"), indent=2)
        print(f"snapshot saved to {SNAP} ({len(cur)} skills)")

if __name__ == "__main__":
    main()
