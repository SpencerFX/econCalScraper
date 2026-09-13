"""
Scrapes FXStreet's economic calendar (https://www.fxstreet.com/economic-calendar)
for a given year and saves one CSV per month.

Data source: the public JSON API that backs the FXStreet calendar widget
(calendar-api.fxstreet.com). No API key is required for this endpoint - it's
the same one the public web page calls in the browser.

Usage:
    python scrape_calendar.py [year] [--out-dir data] [--delay 1.5]

Defaults to the current year if none is given.
"""

import argparse
import calendar
import csv
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

API_BASE = "https://calendar-api.fxstreet.com/en/api/v1"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://www.fxstreet.com/economic-calendar",
    "Accept": "application/json",
}

CSV_FIELDS = [
    "date_utc",
    "time_utc",
    "country",
    "currency",
    "category",
    "event",
    "importance",
    "actual",
    "consensus",
    "previous",
    "revised",
    "unit",
    "potency",
    "is_all_day",
    "is_tentative",
    "is_preliminary",
    "is_report",
    "is_speech",
    "event_id",
]


def fetch_categories(session):
    """Return a dict mapping categoryId -> human readable category name."""
    resp = session.get(f"{API_BASE}/categories", headers=HEADERS, timeout=30)
    resp.raise_for_status()
    return {c["id"]: c["name"] for c in resp.json()}


def fetch_month_events(session, year, month):
    """Fetch all calendar events for the given year/month."""
    days_in_month = calendar.monthrange(year, month)[1]
    start = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    end = datetime(year, month, days_in_month, 23, 59, 59, tzinfo=timezone.utc)

    start_str = start.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S.999Z")

    url = f"{API_BASE}/eventDates/{start_str}/{end_str}"
    resp = session.get(url, headers=HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.json()


def to_row(event, categories):
    date_utc = event.get("dateUtc") or ""
    date_part, time_part = "", ""
    if date_utc:
        dt = datetime.fromisoformat(date_utc.replace("Z", "+00:00"))
        date_part = dt.strftime("%Y-%m-%d")
        time_part = dt.strftime("%H:%M")

    return {
        "date_utc": date_part,
        "time_utc": time_part,
        "country": event.get("countryCode") or "",
        "currency": event.get("currencyCode") or "",
        "category": categories.get(event.get("categoryId"), ""),
        "event": event.get("name") or "",
        "importance": event.get("volatility") or "",
        "actual": event.get("actual"),
        "consensus": event.get("consensus"),
        "previous": event.get("previous"),
        "revised": event.get("revised"),
        "unit": event.get("unit") or "",
        "potency": event.get("potency") or "",
        "is_all_day": event.get("isAllDay"),
        "is_tentative": event.get("isTentative"),
        "is_preliminary": event.get("isPreliminary"),
        "is_report": event.get("isReport"),
        "is_speech": event.get("isSpeech"),
        "event_id": event.get("eventId") or "",
    }


def write_month_csv(rows, out_path):
    rows.sort(key=lambda r: (r["date_utc"], r["time_utc"]))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "year", nargs="?", type=int, default=datetime.now().year,
        help="Year to scrape (default: current year)",
    )
    parser.add_argument(
        "--out-dir", default="data",
        help="Directory (relative to this script) to write monthly CSVs into",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Seconds to wait between monthly requests (politeness delay)",
    )
    args = parser.parse_args()

    out_dir = Path(__file__).resolve().parent / args.out_dir / str(args.year)

    session = requests.Session()

    print(f"Fetching category list...")
    categories = fetch_categories(session)

    for month in range(1, 13):
        print(f"Fetching {args.year}-{month:02d}...", end=" ", flush=True)
        try:
            events = fetch_month_events(session, args.year, month)
        except requests.HTTPError as e:
            print(f"FAILED ({e})")
            continue

        rows = [to_row(e, categories) for e in events]
        out_path = out_dir / f"{args.year}-{month:02d}.csv"
        write_month_csv(rows, out_path)
        print(f"{len(rows)} events -> {out_path.relative_to(Path(__file__).resolve().parent)}")

        if month < 12:
            time.sleep(args.delay)

    print("Done.")


if __name__ == "__main__":
    sys.exit(main())
