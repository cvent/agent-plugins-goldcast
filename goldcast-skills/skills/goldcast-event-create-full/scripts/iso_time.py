#!/usr/bin/env python3
"""Convert between local times and the ISO 8601 strings Goldcast expects.

Why this exists: Goldcast's create_event takes ISO 8601 with a numeric offset (or Z), and
the offset changes with daylight saving. Computing it by hand is the most common way to
schedule an event an hour off. This script does it deterministically.

Mode 1, local -> ISO (for tool calls):
  python iso_time.py --date 2026-11-05 --time 11:00 --tz America/New_York --duration-min 60
  python iso_time.py --date 2026-11-05 --time 11:00 --tz ET --end-time 12:00
  python iso_time.py --date 2026-11-05 --time 11:00 --tz PT --end-date 2026-11-06 --end-time 15:00

  Output: JSON with startTime, endTime (offset form), UTC equivalents, the IANA tz id, the
  weekday, a plain-language `display` string for the user, and warnings (past date,
  ambiguous abbreviation, nonexistent/ambiguous DST time).

Mode 2, UTC -> plain language (for showing times Goldcast returns):
  python iso_time.py --utc 2026-10-22T04:00:00Z --tz America/New_York
  python iso_time.py --utc 2026-10-22T04:00:00Z --utc-end 2026-10-22T05:00:00Z --tz ET

  Output: JSON with the local ISO time(s) and a `display` string.
"""

import argparse
import json
import sys
from datetime import UTC, datetime, timedelta

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    print(json.dumps({"error": "zoneinfo unavailable (need Python 3.9+)"}))
    sys.exit(1)

# Common abbreviations -> IANA. Abbreviations with real ambiguity are flagged in AMBIGUOUS.
ABBREV = {
    "ET": "America/New_York",
    "EST": "America/New_York",
    "EDT": "America/New_York",
    "CT": "America/Chicago",
    "CST": "America/Chicago",
    "CDT": "America/Chicago",
    "MT": "America/Denver",
    "MST": "America/Denver",
    "MDT": "America/Denver",
    "PT": "America/Los_Angeles",
    "PST": "America/Los_Angeles",
    "PDT": "America/Los_Angeles",
    "AKT": "America/Anchorage",
    "HST": "Pacific/Honolulu",
    "UTC": "UTC",
    "GMT": "Europe/London",
    "BST": "Europe/London",
    "UK": "Europe/London",
    "CET": "Europe/Paris",
    "CEST": "Europe/Paris",
    "EET": "Europe/Athens",
    "IST": "Asia/Kolkata",
    "SGT": "Asia/Singapore",
    "HKT": "Asia/Hong_Kong",
    "JST": "Asia/Tokyo",
    "KST": "Asia/Seoul",
    "AEST": "Australia/Sydney",
    "AEDT": "Australia/Sydney",
    "AWST": "Australia/Perth",
    "NZST": "Pacific/Auckland",
    "NZDT": "Pacific/Auckland",
    "GST": "Asia/Dubai",
    "SAST": "Africa/Johannesburg",
}
AMBIGUOUS = {
    "IST": (
        "IST is India, Ireland, or Israel Standard Time."
        " Defaulted to India (Asia/Kolkata); confirm."
    ),
    "CST": ("CST is US Central or China Standard Time. Defaulted to US Central; confirm."),
    "BST": "BST is British Summer Time (also Bangladesh). Defaulted to London.",
    "GST": "GST is Gulf Standard Time (also South Georgia). Defaulted to Dubai.",
}
# US abbreviations that pin standard vs daylight explicitly; warn if they contradict the date.
FIXED_SUFFIX = {
    "EST": "S",
    "CST": "S",
    "MST": "S",
    "PST": "S",
    "EDT": "D",
    "CDT": "D",
    "MDT": "D",
    "PDT": "D",
}
# Labels to show users for common US zones (say "ET", not "EST"/"EDT").
FRIENDLY = {
    "America/New_York": "ET",
    "America/Chicago": "CT",
    "America/Denver": "MT",
    "America/Los_Angeles": "PT",
    "America/Anchorage": "AKT",
    "Pacific/Honolulu": "HT",
}


def parse_hm(s):
    h, m = s.split(":")
    return int(h), int(m)


def resolve_tz(raw):
    warnings = []
    key = raw.strip()
    upper = key.upper()
    if upper in ABBREV:
        tzid = ABBREV[upper]
        if upper in AMBIGUOUS:
            warnings.append(AMBIGUOUS[upper])
    else:
        tzid = key
    try:
        tz = ZoneInfo(tzid)
    except Exception:
        print(
            json.dumps(
                {"error": f"Unknown timezone '{raw}'. Use an IANA id like America/New_York."}
            )
        )
        sys.exit(2)
    return tz, tzid, upper, warnings


def localize(date_str, time_str, tz):
    y, mo, d = (int(x) for x in date_str.split("-"))
    h, mi = parse_hm(time_str)
    naive = datetime(y, mo, d, h, mi)
    warnings = []
    a = naive.replace(tzinfo=tz, fold=0)
    b = naive.replace(tzinfo=tz, fold=1)
    if a.utcoffset() != b.utcoffset():
        # Either a gap (spring forward) or an overlap (fall back)
        roundtrip = a.astimezone(UTC).astimezone(tz)
        if roundtrip.replace(tzinfo=None) != naive:
            warnings.append(
                f"{date_str} {time_str} does not exist in this timezone (clocks spring forward). "
                f"Shifted to {roundtrip.strftime('%H:%M')}."
            )
            return roundtrip, warnings
        warnings.append(
            f"{date_str} {time_str} happens twice in this timezone (clocks fall back). "
            "Used the first occurrence."
        )
    return a, warnings


def iso(dt):
    return dt.isoformat(timespec="seconds")


def utc_iso(dt):
    return iso(dt.astimezone(UTC)).replace("+00:00", "Z")


def clock(dt):
    """12-hour clock without leading zero, e.g. '2:00 PM'."""
    return dt.strftime("%I:%M %p").lstrip("0")


def day(dt):
    """e.g. 'Thu, Feb 5, 2027'."""
    return f"{dt.strftime('%a, %b')} {dt.day}, {dt.year}"


def display(start, end, tzid):
    """Plain-language range for users, e.g. 'Thu, Feb 5, 2027, 2:00-3:00 PM ET'."""
    label = FRIENDLY.get(tzid) or start.tzname() or tzid
    if end is None:
        return f"{day(start)}, {clock(start)} {label}"
    if start.date() == end.date():
        s, e = clock(start), clock(end)
        if s[-2:] == e[-2:]:  # same AM/PM: '2:00-3:00 PM'
            return f"{day(start)}, {s[:-3]}-{e} {label}"
        return f"{day(start)}, {s}-{e} {label}"
    return f"{day(start)}, {clock(start)} to {day(end)}, {clock(end)} {label}"


def parse_utc(s):
    dt = datetime.fromisoformat(s.strip().replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt


def from_utc(args):
    tz, tzid, _, warnings = resolve_tz(args.tz)
    start = parse_utc(args.utc).astimezone(tz)
    end = parse_utc(args.utc_end).astimezone(tz) if args.utc_end else None
    out = {
        "timezone": tzid,
        "startLocal": iso(start),
        "endLocal": iso(end) if end else None,
        "display": display(start, end, tzid),
        "warnings": warnings,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def to_iso(args):
    tz, tzid, upper, warnings = resolve_tz(args.tz)

    start, w = localize(args.date, args.time, tz)
    warnings += w

    if args.end_time:
        end, w = localize(args.end_date or args.date, args.end_time, tz)
        warnings += w
    else:
        end = (start.astimezone(UTC) + timedelta(minutes=args.duration_min or 60)).astimezone(tz)

    if end <= start:
        warnings.append("End is not after start. Check the end date/time.")

    if upper in FIXED_SUFFIX:
        is_dst = bool(start.dst())
        if (FIXED_SUFFIX[upper] == "D") != is_dst:
            warnings.append(
                f"You wrote {upper}, but on {args.date} this zone is on "
                f"{'daylight' if is_dst else 'standard'} time. Use the real offset "
                f"({start.strftime('%z')}) and say 'ET'/'PT' to the user instead of '{upper}'."
            )

    now = datetime.now(UTC)
    if start.astimezone(UTC) <= now:
        warnings.append("Start time is in the past.")
    elif start.astimezone(UTC) - now < timedelta(hours=24):
        warnings.append("Start is less than 24 hours away. Confirm this is intended.")

    out = {
        "timezone": tzid,
        "weekday": start.strftime("%A"),
        "startTime": iso(start),
        "endTime": iso(end),
        "startUtc": utc_iso(start),
        "endUtc": utc_iso(end),
        "offset": start.strftime("%z"),
        "durationMinutes": int((end - start).total_seconds() // 60),
        "display": display(start, end, tzid),
        "warnings": warnings,
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tz", required=True, help="IANA id (America/New_York) or abbreviation (ET)")
    # Mode 1: local -> ISO
    p.add_argument("--date", help="Local start date YYYY-MM-DD")
    p.add_argument("--time", help="Local start time HH:MM (24h)")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--duration-min", type=int, help="Duration in minutes (default 60)")
    g.add_argument("--end-time", help="Local end time HH:MM (24h)")
    p.add_argument("--end-date", help="Local end date YYYY-MM-DD (defaults to --date)")
    # Mode 2: UTC -> plain language
    p.add_argument("--utc", help="A UTC ISO time from Goldcast, e.g. 2026-10-22T04:00:00Z")
    p.add_argument("--utc-end", help="Optional UTC end time, for a range")
    args = p.parse_args()

    if args.utc:
        from_utc(args)
    elif args.date and args.time:
        to_iso(args)
    else:
        p.error("Give either --date and --time (local -> ISO) or --utc (UTC -> plain language).")


if __name__ == "__main__":
    main()
