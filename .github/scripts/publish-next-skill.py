#!/usr/bin/env python3
"""
Publish the next queued NEW DeepRead skill to ClawHub (one per run).

Reads .github/new-skills-queue.json, finds the FIRST entry whose slug is not yet
on the registry, and publishes that skill folder under its explicit canonical slug.
Posts a note to Slack on success. Idempotent and self-advancing: already-published
slugs are skipped, so re-runs are safe and the queue advances one skill at a time.

Auth: expects `clawhub login --token` to have already run in the workflow.
Env:
  SLACK_WEBHOOK_URL       (optional) post a "new skill published" note
  DEEPREAD_REPORT_UNTIL   (optional) YYYY-MM-DD; stop publishing after this date
"""
import json, os, subprocess, sys, urllib.request, datetime

ROOT  = os.getcwd()
QUEUE = os.path.join(ROOT, ".github", "new-skills-queue.json")
REGISTRY = "https://clawhub.ai/api/v1/skills/{slug}"
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))

def is_published(slug):
    """True if the slug already has a published version on the registry."""
    try:
        req = urllib.request.Request(REGISTRY.format(slug=slug), headers={"User-Agent": "deepread-publish/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return bool((d.get("latestVersion") or {}).get("version"))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return False
        print(f"registry check {slug}: HTTP {e.code} (treating as unpublished)")
        return False
    except Exception as e:
        print(f"registry check {slug} failed: {e} (treating as PUBLISHED to avoid dup-publish)")
        return True  # fail safe: don't risk a duplicate publish on a transient error

def slack(text):
    hook = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not hook:
        return
    try:
        body = json.dumps({"text": text}).encode()
        req = urllib.request.Request(hook, data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        print(f"slack note failed: {e}")

def main():
    # Optional campaign window
    until = os.environ.get("DEEPREAD_REPORT_UNTIL", "").strip()
    if until:
        try:
            if datetime.datetime.now(IST).date() > datetime.date.fromisoformat(until):
                print(f"Campaign window ended ({until}); not publishing. Bump DEEPREAD_REPORT_UNTIL to extend.")
                return
        except ValueError:
            pass

    q = json.load(open(QUEUE))
    skills = q.get("skills", [])
    total = len(skills)
    done = 0

    for e in skills:
        slug, folder = e["slug"], e["folder"]
        if is_published(slug):
            done += 1
            continue

        path = os.path.join(ROOT, "skills", folder)
        if not os.path.isdir(path):
            print(f"ERROR: skill folder missing: {path}"); sys.exit(1)

        print(f"Publishing NEW skill: {slug}  (from skills/{folder})")
        cmd = ["npx", "-y", "clawhub@latest", "publish", path,
               "--slug", slug, "--version", "1.0.0",
               "--changelog", e.get("changelog", "Initial release."),
               "--tags", "latest"]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        print(r.stdout[-2000:]); print(r.stderr[-2000:], file=sys.stderr)
        if r.returncode != 0:
            slack(f":warning: DeepRead: failed to publish *{slug}* to ClawHub — check the Action log.")
            sys.exit(1)

        n = done + 1
        slack(
            f":package: *New DeepRead skill published to ClawHub — {n}/{total}*\n"
            f"*{e['name']}*  (`{slug}`)\n"
            f"{e.get('changelog','')}\n"
            f"<https://clawhub.ai/skills/{slug}|View on ClawHub>  ·  "
            f"`clawhub install uday390/{slug}`"
        )
        print(f"✅ published {slug}")
        return

    msg = f"All {total} queued skills are already published. Add more to .github/new-skills-queue.json to continue."
    print(msg)
    slack(f":information_source: DeepRead ClawHub queue empty — all {total} skills published. Add more to keep the daily posts going.")

if __name__ == "__main__":
    main()
