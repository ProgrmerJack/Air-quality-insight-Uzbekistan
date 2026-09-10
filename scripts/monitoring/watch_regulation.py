#!/usr/bin/env python3
"""
watch_regulation.py -- daily watch on regulation.gov.uz for the consolidated air-quality act.

Missing the public-comment window is the main way docs/MINISTRY_ENGAGEMENT_PLAN.md fails.
A weekly manual check is not enough: comment windows on Uzbek draft normative acts can be
as short as 15 days and may open over a holiday. The target is the single act linking air
quality to mandatory action across government bodies, due for submission by 30 Dec 2026,
so a public-discussion draft could appear from around October.

NO BROWSER NEEDED. regulation.gov.uz is server-rendered Yii, not a JavaScript SPA: the
document list is in the initial HTML. Earlier drafts of this watcher used Playwright
against /uz/documents and /uz/d/new -- both of which 404. They "ran fine" and reported
nothing forever, which is the exact failure this script exists to prevent. Two guards now:
  * every source must yield >= MIN_ROWS documents or the run reports SOURCE BROKEN;
  * --selftest checks the parser against the live portal without touching state.

Two detection strategies, because keyword matching alone is fragile:
  * category 14 (Atrof tabiiy muhit va tabiiy resurslar) is low-volume, so ANY new
    document there is worth a look -- no keyword needed;
  * the general index is keyword-filtered, to catch an act filed under another category.

    pip install requests
    python scripts/monitoring/watch_regulation.py --selftest   # check parser vs live site
    python scripts/monitoring/watch_regulation.py --once       # first run: records baseline

Schedule daily:
    Windows: schtasks /create /tn "regulation-watch" /sc daily /st 09:00 ^
             /tr "python C:\\path\\to\\scripts\\monitoring\\watch_regulation.py"
    cron:    0 9 * * * cd /path/to/repo && python3 scripts/monitoring/watch_regulation.py

Alerting -- set either group as environment variables. Without them it prints only.
    TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID     (recommended: instant, reaches a phone)
    SMTP_HOST, SMTP_USER, SMTP_PASS, ALERT_TO (SMTP_PORT optional, default 587)
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import smtplib
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("! pip install requests")

BASE = "https://regulation.gov.uz"
IDX = "/document/index"

# (label, path, alert_on_every_new_document)
SOURCES = [
    ("environment oz", f"/oz{IDX}?GlobalSearch%5Bcategory_id%5D=14", True),
    ("environment ru", f"/ru{IDX}?GlobalSearch%5Bcategory_id%5D=14", True),
    ("health oz",      f"/oz{IDX}?GlobalSearch%5Bcategory_id%5D=15", False),
    ("education oz",   f"/oz{IDX}?GlobalSearch%5Bcategory_id%5D=6",  False),
    ("all recent oz",  f"/oz{IDX}", False),
    ("all recent ru",  f"/ru{IDX}", False),
]
MIN_ROWS = 5  # a healthy index page returns 20; below this the parser or site has changed

# Latin Uzbek, Cyrillic Uzbek and Russian. A draft consolidating measures across agencies
# may be titled around "atmosfera havosi" rather than "havo sifati" -- keep this broad and
# cut noise by reading the hits, not by narrowing the list.
KEYWORDS = [
    "havo sifati", "atmosfera havosi", "havoni muhofaza", "ifloslanish", "toza havo",
    "ekologiya", "atrof-muhit", "atrof tabiiy muhit", "chang", "zararli moddalar",
    "maktab", "ta'lim muassasa", "taʼlim muassasa", "bolalar",
    "ҳаво сифати", "атмосфера ҳавоси", "ифлосланиш", "экология", "мактаб",
    "качество воздуха", "атмосферного воздуха", "атмосферный воздух", "атмосферу",
    "загрязнени", "эколог", "охрана воздуха", "чистый воздух", "школ",
    "air quality", "atmospheric air",
]

STATE = Path(__file__).with_name(".regulation_seen.json")
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

# <tr data-key="105513"><td>1</td><td class="col-md-3"><a href="/oz/d/105513">TITLE <span>...
ROW_RE = re.compile(r'href="(/(?:oz|uz|ru)/d/(\d+)[^"]*)"[^>]*>\s*(.*?)\s*(?:<span|</a>)',
                    re.S)


def clean(t: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def fetch(path: str, timeout: int = 45) -> list[dict]:
    r = requests.get(BASE + path, headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    out, seen = [], set()
    for href, doc_id, raw in ROW_RE.findall(r.text):
        title = clean(raw)
        if len(title) < 15 or doc_id in seen:
            continue
        seen.add(doc_id)
        out.append({"id": doc_id, "title": title, "href": BASE + href})
    return out


def matches(title: str) -> list[str]:
    low = title.lower()
    return [k for k in KEYWORDS if k.lower() in low]


def load_seen() -> dict:
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            print("! state file corrupt, starting fresh", file=sys.stderr)
    return {}


def telegram(text: str) -> bool:
    tok, chat = os.getenv("TELEGRAM_BOT_TOKEN"), os.getenv("TELEGRAM_CHAT_ID")
    if not (tok and chat):
        return False
    data = urllib.parse.urlencode({"chat_id": chat, "text": text[:4000],
                                   "disable_web_page_preview": "true"}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage",
                               data=data, timeout=20)
        return True
    except Exception as e:                                            # noqa: BLE001
        print(f"! telegram failed: {e}", file=sys.stderr)
        return False


def email(subject: str, body: str) -> bool:
    host, user, pwd, to = (os.getenv("SMTP_HOST"), os.getenv("SMTP_USER"),
                           os.getenv("SMTP_PASS"), os.getenv("ALERT_TO"))
    if not all((host, user, pwd, to)):
        return False
    m = EmailMessage()
    m["Subject"], m["From"], m["To"] = subject, user, to
    m.set_content(body)
    try:
        with smtplib.SMTP(host, int(os.getenv("SMTP_PORT", "587")), timeout=30) as s:
            s.starttls(); s.login(user, pwd); s.send_message(m)
        return True
    except Exception as e:                                            # noqa: BLE001
        print(f"! email failed: {e}", file=sys.stderr)
        return False


def run(dry: bool, reset: bool) -> int:
    if reset and STATE.exists():
        STATE.unlink(); print("state reset")

    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n=== regulation.gov.uz watch -- {stamp} ===")
    seen = load_seen()
    first_run = not seen

    hits, broken, total = {}, [], 0
    for label, path, alert_all in SOURCES:
        try:
            docs = fetch(path)
        except Exception as e:                                        # noqa: BLE001
            broken.append(f"{label}: {type(e).__name__} {e}")
            print(f"  {label:16s} ERROR {type(e).__name__}")
            continue
        total += len(docs)
        if len(docs) < MIN_ROWS:
            broken.append(f"{label}: only {len(docs)} rows (expected >= {MIN_ROWS})")
        print(f"  {label:16s} {len(docs):3d} documents")
        for d in docs:
            kws = matches(d["title"])
            if not (alert_all or kws) or d["id"] in seen or d["id"] in hits:
                continue
            hits[d["id"]] = {**d, "keywords": kws,
                             "why": "environment category" if alert_all and not kws
                                    else ", ".join(kws)}
        for d in docs:
            seen.setdefault(d["id"], {"title": d["title"], "first_seen": stamp,
                                      "href": d["href"]})

    if broken:
        # Loud, because the silent version of this failure is the whole risk.
        print("\n!! SOURCE BROKEN -- this watcher may be blind:")
        for b in broken:
            print(f"     {b}")
        print("     Check https://regulation.gov.uz/oz/document/index by hand and fix SOURCES/ROW_RE.")

    print(f"\n{total} rows scanned, {len(hits)} new item(s) of interest")

    if first_run:
        print("\nFirst run -- baseline recorded. Currently on the portal and matching:")
        for d in hits.values():
            print(f"  - [{d['why']}] {d['title'][:100]}")
        print("\nFuture runs alert only on documents that appear after today.")
        hits = {}

    if hits:
        lines = [f"AIR QUALITY DRAFT WATCH -- {len(hits)} new on regulation.gov.uz", ""]
        for d in hits.values():
            lines += [f"* {d['title']}", f"  why: {d['why']}", f"  {d['href']}", ""]
        lines += ["Target: the consolidated act linking air quality to mandatory actions for",
                  "all government bodies, due for submission by 30 December 2026.", "",
                  "If this is it: submit the indoor-classroom clause within 72 hours.",
                  "Comment windows can be as short as 15 days."]
        body = "\n".join(lines)
        print("\n" + body)
        if not dry:
            sent = [n for n, ok in (("telegram", telegram(body)),
                                    ("email", email("regulation.gov.uz: air-quality draft", body)))
                    if ok]
            print(f"\nalerts sent: {', '.join(sent) if sent else 'none configured'}")
            if not sent:
                print("  set TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID, or SMTP_* + ALERT_TO")

    if not dry:
        STATE.write_text(json.dumps(seen, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if broken else 0


def selftest() -> int:
    """Check keyword logic offline, then the parser against the live portal."""
    assert matches("Атмосферного воздуха ҳақида"), "russian keyword missed"
    assert matches("Havo sifati toʻgʻrisidagi nizom"), "latin uzbek keyword missed"
    assert not matches("Daktiloskopik ro'yxatga olish"), "unrelated title matched"
    assert clean("Title <span>x</span>  \n b") == "Title x b", "clean() wrong"
    print("offline checks ok")

    bad = 0
    for label, path, _ in SOURCES:
        try:
            docs = fetch(path)
        except Exception as e:                                        # noqa: BLE001
            print(f"  FAIL {label}: {type(e).__name__} {e}"); bad += 1; continue
        status = "ok  " if len(docs) >= MIN_ROWS else "THIN"
        if len(docs) < MIN_ROWS:
            bad += 1
        print(f"  {status} {label:16s} {len(docs):3d} docs   e.g. {docs[0]['title'][:60] if docs else '-'}")
    print("selftest PASSED" if not bad else f"selftest FAILED ({bad} source(s))")
    return bad and 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true", help="accepted for cron symmetry; a run is always one pass")
    ap.add_argument("--dry-run", action="store_true", help="do not send alerts or save state")
    ap.add_argument("--reset", action="store_true", help="clear the seen-documents baseline")
    ap.add_argument("--selftest", action="store_true", help="verify parser against the live portal")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else run(a.dry_run, a.reset))
