#!/usr/bin/env python3
"""Compare MAUDE aggregations between a prior and a recent period and flag signals.

Usage (either form):
    python compare_periods.py --recent recent.json --prior prior.json \
        --recent-dates 2026-05-01:2026-10-30 --prior-dates 2025-10-31:2026-04-30 \
        [--code DZE] [--threshold 20] [--low-count 5] [--json-out flags.json]
    python compare_periods.py input.json [options]

recent.json / prior.json: the usfda_maude_search response for each period, saved as
returned (the object with "data" -> "total_count" and "aggregations"), or just its
"data" object.

input.json:
{
  "product_code": "DZE",
  "recent": {"start": "2026-05-22", "end": "2026-11-22", "total_count": 1234,
             "aggregations": {"device_problem": [{"value": "...", "count": 1}, ...],
                              "patient_problem": [...], "event_type": [...]}},
  "prior":  {... same shape ...}
}

Prints Markdown tables to stdout. Optionally writes the full comparison as JSON.
"""
import argparse
import json
import sys

DIMENSIONS = [
    ("event_type", "Event types"),
    ("device_problem", "Device problems"),
    ("patient_problem", "Patient problems"),
]

# Codes that say little about a specific failure or harm. They are still compared,
# but marked so the reader does not mistake them for a specific signal.
GENERIC_TERMS = {
    "adverse event without identified device or use problem",
    "insufficient information",
    "appropriate term/code not available",
    "no clinical signs, symptoms or conditions",
    "no known impact or consequence to patient",
    "no consequences or impact to patient",
    "no patient involvement",
    "no apparent adverse event",
    "appropriate clinical signs, symptoms, conditions term / code not available",
    "no code available",
    "no information",
}


def to_counts(buckets):
    out = {}
    for b in buckets or []:
        name = str(b.get("value", "")).strip()
        if name:
            out[name] = out.get(name, 0) + int(b.get("count", 0))
    return out


def pct(n, d):
    return None if not d else 100.0 * n / d


def fmt_pct(x, signed=False):
    if x is None:
        return "n/a"
    if signed:
        return f"{x:+.0f}%"
    if x == 0:
        return "0%"
    if x < 0.01:
        return "<0.01%"
    return f"{x:.2f}%" if x < 1 else f"{x:.1f}%"


BUCKET_LIMIT = 100  # NyquistAI returns at most this many terms per aggregation


def compare_dimension(prior, recent, prior_total, recent_total, threshold, low_count):
    # If the prior list hit the bucket limit, a term missing from it may simply be
    # below the smallest count shown, so it cannot be called "new" with confidence.
    prior_truncated = len(prior) >= BUCKET_LIMIT
    prior_floor = min(prior.values()) if prior else 0
    rows = []
    for term in set(prior) | set(recent):
        p, r = prior.get(term, 0), recent.get(term, 0)
        change = None if p == 0 else 100.0 * (r - p) / p
        share_p, share_r = pct(p, prior_total), pct(r, recent_total)
        share_delta = (share_r or 0) - (share_p or 0)
        flags = []
        notes = []
        if p == 0 and r > 0:
            flags.append("NEW")
            if prior_truncated:
                notes.append(f"prior list truncated: prior count unknown, below {prior_floor}")
        elif change is not None and change > threshold:
            flags.append("INCREASE")
        if flags and r < low_count:
            notes.append("low count")
        if term.lower() in GENERIC_TERMS:
            notes.append("generic code")
        rows.append({
            "term": term, "prior": p, "recent": r, "change_pct": change,
            "share_prior_pct": share_p, "share_recent_pct": share_r,
            "share_change_pts": share_delta, "flags": flags, "notes": notes,
        })
    return rows


def md_table(rows):
    lines = ["| Term | Prior | Recent | Change | Share prior → recent | Notes |",
             "|---|---:|---:|---:|---|---|"]
    for x in rows:
        change = "new" if "NEW" in x["flags"] else fmt_pct(x["change_pct"], signed=True)
        share = f"{fmt_pct(x['share_prior_pct'])} → {fmt_pct(x['share_recent_pct'])}"
        lines.append(f"| {x['term']} | {x['prior']:,} | {x['recent']:,} | {change} | {share} | {', '.join(x['notes'])} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?")
    ap.add_argument("--recent")
    ap.add_argument("--prior")
    ap.add_argument("--recent-dates", default=":")
    ap.add_argument("--prior-dates", default=":")
    ap.add_argument("--code")
    ap.add_argument("--threshold", type=float, default=20.0, help="percent increase that counts as a signal")
    ap.add_argument("--low-count", type=int, default=5, help="flagged terms with fewer recent reports are marked 'low count'")
    ap.add_argument("--json-out")
    a = ap.parse_args()

    if a.recent and a.prior:
        def load(path, dates):
            raw = json.load(open(path))
            d = raw.get("data", raw)
            start, _, end = dates.partition(":")
            return {"start": start, "end": end, "total_count": d["total_count"],
                    "aggregations": d.get("aggregations", {})}
        data = {"product_code": a.code, "recent": load(a.recent, a.recent_dates),
                "prior": load(a.prior, a.prior_dates)}
    elif a.input:
        data = json.load(open(a.input))
    else:
        ap.error("give input.json, or --recent and --prior")
    pr, rc = data["prior"], data["recent"]
    pt, rt = int(pr["total_count"]), int(rc["total_count"])
    vol_change = pct(rt - pt, pt)

    out = {"product_code": data.get("product_code"), "prior_total": pt, "recent_total": rt,
           "volume_change_pct": vol_change, "threshold": a.threshold, "low_count": a.low_count,
           "dimensions": {}}

    print(f"## Volume\n\nPrior period ({pr.get('start')} to {pr.get('end')}): {pt:,} reports  ")
    print(f"Recent period ({rc.get('start')} to {rc.get('end')}): {rt:,} reports  ")
    print(f"Change in total reports: {fmt_pct(vol_change, signed=True)}\n")

    for key, label in DIMENSIONS:
        rows = compare_dimension(to_counts(pr["aggregations"].get(key)), to_counts(rc["aggregations"].get(key)),
                                 pt, rt, a.threshold, a.low_count)
        out["dimensions"][key] = rows
        for side, agg in (("prior", pr), ("recent", rc)):
            if len(agg["aggregations"].get(key) or []) >= BUCKET_LIMIT:
                print(f"> Note: the {side} {label.lower()} list has {BUCKET_LIMIT} terms, the most the tool returns, so rarer terms are missing from it.\n")
        new = sorted([x for x in rows if "NEW" in x["flags"]], key=lambda x: -x["recent"])
        inc = sorted([x for x in rows if "INCREASE" in x["flags"]], key=lambda x: -(x["recent"] - x["prior"]))
        print(f"## {label}\n")
        print(f"### New in recent period ({len(new)})\n")
        print(md_table(new) if new else "None.")
        print(f"\n### Increase greater than {a.threshold:g}% ({len(inc)})\n")
        print(md_table(inc) if inc else "None.")
        print()

    if a.json_out:
        json.dump(out, open(a.json_out, "w"), indent=2)


if __name__ == "__main__":
    sys.exit(main())
