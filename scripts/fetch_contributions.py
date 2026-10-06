#!/usr/bin/env python3
"""
Scrape daily contribution counts from GitHub's public unauthenticated
contributions endpoint (the same fragment the profile page uses) and
write data/contributions.json with raw days plus derived stats.

No token, no auth, no GraphQL — just the public HTML GitHub already serves.
Run daily by .github/workflows/update-profile-art.yml.
"""
import datetime
import json
import os
import re
import sys
import requests
from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
USERNAME = os.environ.get("GH_PROFILE_USER", "RohanDas28")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUT_PATH = os.path.join(HERE, "..", "data", "contributions.json")


def fetch_days():
    print(f"Fetching public contribution data for {USERNAME} from {URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    resp = requests.get(URL, headers=headers, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    cells = soup.select("td.ContributionCalendar-day")
    if not cells:
        print("no calendar cells found -- github markup may have changed", file=sys.stderr)
        # Try fallback or jogruber API if available
        api_url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y=last"
        try:
            r = requests.get(api_url, timeout=20)
            if r.status_code == 200:
                api_data = r.json()
                days = []
                for d in api_data.get("contributions", []):
                    days.append({"date": d["date"], "count": d["count"], "level": d["level"]})
                days.sort(key=lambda d: d["date"])
                return days
        except Exception as e:
            print(f"Fallback API failed: {e}", file=sys.stderr)
        sys.exit(1)

    days = []
    for td in cells:
        date = td.get("data-date")
        if not date:
            continue
        td_id = td.get("id")
        tooltip_el = soup.find("tool-tip", attrs={"for": td_id}) if td_id else None
        text = tooltip_el.get_text(strip=True) if tooltip_el else ""
        
        # In newer github markup, text could be in aria-label or child elements
        if not text:
            text = td.get("aria-label", "") or td.get_text(strip=True)

        if re.search(r"no contributions", text, re.I):
            count = 0
        else:
            m = re.search(r"(\d+)\s+contribution", text, re.I)
            if not m:
                m = re.match(r"(\d+)", text)
            count = int(m.group(1)) if m else 0
        
        level = int(td.get("data-level") or 0)
        days.append({"date": date, "count": count, "level": level})

    days.sort(key=lambda d: d["date"])
    return days


def compute_current_streak(days):
    if not days:
        return 0, None, None
    idx = len(days) - 1
    if days[idx]["count"] == 0:
        idx -= 1  # today isn't over yet -- don't break the streak on it
    streak = 0
    end_idx = idx
    while idx >= 0 and days[idx]["count"] > 0:
        streak += 1
        idx -= 1
    start_idx = idx + 1
    if streak == 0:
        return 0, None, None
    return streak, days[start_idx]["date"], days[end_idx]["date"]


def compute_longest_streak(days):
    longest = run = 0
    longest_start = longest_end = None
    run_start_idx = None
    for i, d in enumerate(days):
        if d["count"] > 0:
            if run == 0:
                run_start_idx = i
            run += 1
            if run > longest:
                longest = run
                longest_start = days[run_start_idx]["date"]
                longest_end = days[i]["date"]
        else:
            run = 0
    return longest, longest_start, longest_end


def build_data(days):
    total = sum(d["count"] for d in days)
    active_days = sum(1 for d in days if d["count"] > 0)
    best = max(days, key=lambda d: d["count"]) if days else {"date": "—", "count": 0}
    cur_len, cur_start, cur_end = compute_current_streak(days)
    long_len, long_start, long_end = compute_longest_streak(days)

    monthly = {}
    for d in days:
        key = d["date"][:7]
        monthly[key] = monthly.get(key, 0) + d["count"]
    monthly_list = [{"month": k, "total": v} for k, v in sorted(monthly.items())]

    return {
        "username": USERNAME,
        "generated_at": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "range": {"start": days[0]["date"], "end": days[-1]["date"]} if days else {"start": "—", "end": "—"},
        "total_contributions": total,
        "active_days": active_days,
        "avg_per_active_day": round(total / active_days, 1) if active_days else 0,
        "current_streak": {"length": cur_len, "start": cur_start, "end": cur_end},
        "longest_streak": {"length": long_len, "start": long_start, "end": long_end},
        "best_day": {"date": best["date"], "count": best["count"]},
        "monthly": monthly_list,
        "days": days,
    }


if __name__ == "__main__":
    days = fetch_days()
    data = build_data(days)
    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote {OUT_PATH}: {data['total_contributions']} contributions, "
          f"current streak {data['current_streak']['length']} days, "
          f"longest streak {data['longest_streak']['length']} days")
