---
name: "maude-signal-detection"
description: Detect emerging signals and trends in FDA MAUDE adverse event reports for a medical device product code by comparing the most recent 6 months against the prior 6 months, pulled through the NyquistAI connector, and deliver a Markdown signal report. Flags device problems, patient problems and event types (deaths, injuries, malfunctions) that are new in the recent period or up more than 20%, and checks whether each signal is driven by one manufacturer. Use this skill whenever the user gives a 3-letter FDA product code (e.g. DZE, LLZ, NIQ) or a device type and asks about signal detection, emerging trends, what changed recently, new failure modes, spikes or increases in adverse events, period-over-period or half-year MAUDE comparison, or post-market trend monitoring, even if they don't say "signal". Prefer this over a general risk or hazard analysis whenever the question is about change over time rather than the overall risk profile.
compatibility: Requires the NyquistAI connector (usfda_maude_search with the event_type filter; usfda_device_search to look up a product code). Load them with tool_search if deferred. Uses Python 3 for the bundled comparison script.
---

# MAUDE Signal Detection

Find out what changed in MAUDE adverse event reporting for one product code: which problems are new, which are growing, whether deaths or serious injuries are moving, and whether a change is field-wide or one manufacturer's reporting. The reader is usually someone in regulatory, quality or post-market surveillance deciding what needs a closer look. So rank what deserves attention, give exact numbers, and be candid about how much of a change could be a reporting artifact. MAUDE trends are full of artifacts: bulk filings, miscoded deaths, one firm changing how it codes complaints. Telling those apart from real shifts is most of the value of this report.

## Inputs

- **Product code** (required): a 3-letter FDA product code. Uppercase it. If the user names a device type instead, call `usfda_device_search` with the device type as `query` (add `medical_specialty` if obvious) and `size: 3`. Its `product_code` aggregation shows which codes match. Tell the user the most likely code, what it covers and an example device, and ask them to confirm before pulling data. The wrong code produces a confident report about the wrong devices.
- **Periods** (default): recent = the 6 months ending at the data cutoff; prior = the 6 months before that. Use the user's windows if they give different ones, keeping both the same length so counts are comparable.
- **Thresholds** (default): an increase of more than 20% counts as a signal; flagged items with fewer than 5 reports in the recent period are marked "low count". Use the user's numbers if they give them.

## How the MAUDE tool behaves (learned from testing)

- **Aggregations count every matching report**, not just the returned rows, and `total_count` is the report total. Use `size: 1`; never page through records to count them.
- **Aggregation lists stop at 100 terms.** If a prior-period list has 100 entries, a term missing from it may only be below the smallest count shown, so it can't be called "new" with confidence. The script detects this and says so.
- **Queries are AND by default.** `"death expired died"` matches only reports containing all three words, which is usually none.
- **A term in double quotes gives an exact count.** A `query` of `"\"Bacterial Infection\""` with the same product code and dates returns exactly the reports with that term. Its aggregations show which other problems occur alongside it.
- **Adding a firm name gives that firm's exact count:** `"\"Bacterial Infection\" Adin"`. A bare firm name (`"Insulet"`) counts that firm's reports overall.
- **`event_type` filters by event type** (`"Death"`, `"Injury"`, `"Malfunction"`, `"Other"`) and combines with `query`, `product_code` and dates. With `event_type: "Death"` and `query: ""` you get exactly the death-coded reports; with `event_type: "Injury"` and a firm name you get that firm's injury count. The aggregations of a filtered call show which problems drive that event type.
- **A query with no product code times out.** Always filter by product code.

## Step 1: Set the windows

Find the data cutoff. MAUDE arrives in batches, and a recent window that runs past the newest data looks artificially small and hides real increases. Call `usfda_maude_search` with `query: ""`, the `product_code`, `sort_by: "date_received"`, `sort_order: "desc"`, `size: 1`. The returned `date_received` is the newest report for this code.

- If it's within ~45 days of today, end the recent window at that date and say so in the report. (In testing, the newest data was 23 days old for both high- and moderate-volume codes.)
- If it's older than that, the code may simply be quiet. End the window today and mention the gap.

Then set: recent = (end − 6 months + 1 day) to end; prior = the 6 months immediately before, ending the day before recent starts. Use full-day ISO datetimes (`...T00:00:00Z` to `...T23:59:59Z`).

## Step 2: Pull the two periods

Call `usfda_maude_search` once per period with `query: ""`, `product_code`, the period's `date_received_from` / `date_received_to`, and `size: 1`. If a period returns zero reports, say so. If both are zero, check the product code and stop with a short note rather than an empty report.

## Step 3: Compare with the bundled script

Save each response as returned to a JSON file (e.g. `/home/claude/work/recent.json` and `prior.json`; the whole response or just its `data` object both work). Always use absolute paths, because relative paths can land in an unexpected working directory. Then run:

```bash
python /path/to/skill/scripts/compare_periods.py \
  --recent /home/claude/work/recent.json --prior /home/claude/work/prior.json \
  --recent-dates 2026-05-01:2026-10-30 --prior-dates 2025-10-31:2026-04-30 \
  --code DZE --threshold 20 --low-count 5 --json-out /home/claude/work/flags.json
```

Use the script rather than computing by hand. Percentages across dozens of terms drift when done mentally, and a signal report is only useful if its numbers are right. The output gives, for event types, device problems and patient problems: new terms and terms up more than the threshold, sorted by size, with share of total in both periods, and notes for low counts, generic codes and truncated lists.

## Step 4: Interpret the flags

The script finds candidates; your job is to say which ones matter.

- **Compare with overall volume.** If total reports rose 40%, a term up 25% is losing ground. Look at the share column. A term whose share rose is a stronger signal than one that rose with everything else.
- **Deaths and injuries are covered in Step 5**, whatever the script flags.
- **Clusters.** Terms that rise together are usually one story. In testing, Vomiting, Dizziness and Nausea rose because Diabetic Ketoacidosis reports list them together. Check co-occurrence with a quoted-term search and report the cluster once.
- **Coding shifts.** Near-synonyms trade counts ("Failure of Implant" falling while "Inadequate Osseointegration" rises). Mention a likely coding shift rather than reporting two signals.
- **Implausible terms** for the device type (e.g. "Operating System Becomes Nonfunctional" or "Encephalocele" for dental implants) are usually miscoding. Group them in one line and don't rank them as signals.
- **Low counts.** Keep them in the report, as the user asked, but compactly. Don't lead with a jump from 1 to 3 unless it's clinically serious (coma, fire, death).
- **Generic codes** ("Insufficient Information", "No Clinical Signs, Symptoms or Conditions", etc.) rising usually reflects how reports are filed. Mention them briefly.

## Step 5: Review deaths and injuries

Do this for every report, whether or not the script flagged them, because deaths are what readers most need to get right and counts alone can mislead.

**Deaths.** Call `usfda_maude_search` with `query: ""`, the product code, the recent-period dates, `event_type: "Death"`, `show_details: true`, `size: 25`, `sort_by: "date_received"`. Read every narrative (if there are more than 25, read the 25 most recent and use the aggregations for the rest). Sort each into one of three kinds:
- **Plausibly device-related:** a device problem is described, or the firm can't rule one out and the clinical story fits a device failure (e.g. ketoacidosis in an insulin pump user).
- **Unrelated or unknown:** e.g. an accident, a death reported with no details, or the device not in use.
- **Miscoded:** the narrative describes no death at all. In testing, all four dental implant "deaths" were routine implant failures coded as deaths by mistake.
Report the count of each kind, a one-line paraphrase per report, and links. If the recent period has deaths, run the same call for the prior period (`size: 25`) so the comparison is between like and like, not just raw counts.

**Injuries.** If the injury count or share rose, call with `event_type: "Injury"` (`size: 1`) for each period and compare the patient problem aggregations. They show which harms drive the change, more directly than reading terms from the full report set. If one firm dominates, add the firm name as `query` in both periods to see whether its injuries grew faster than its overall reports.

## Step 6: Look behind the other top signals

Counts show that something moved; these checks show why. Pick the 3–5 most important remaining signals and, for each:

1. **Read examples:** `query` = the exact term in double quotes, same product code and recent dates, `show_details: true`, `size: 5`, `sort_by: "_score"`. Read the narratives: what failed, what happened to the patient, whether a device link is claimed or ruled out, whether the report was filed "out of caution".
2. **Check manufacturer concentration:** note the dominant firm in the sample, then get exact counts with `"\"<term>\" <firm>"` (size 1). Compare that firm's share of the signal with its share of all reports (query `"<firm>"` alone, size 1) and, when it matters, with the prior period. 95 of 95 reports from one firm that files 5% of reports is a reporting artifact or a firm-specific issue. 85% from a firm that files 59% of reports, with that firm's injuries up 65% against 7% volume growth, is a real shift within that firm's reports. Spell out which the evidence supports.

Keep it efficient: a handful of calls per signal is enough. Record report numbers and `official_url` links for the examples you cite.

## Step 7: Write the report

Write a Markdown file named `maude-signals-<CODE>-<YYYY-MM-DD>.md` in the outputs folder, present it to the user, and give a two- or three-sentence summary in chat. Use this structure:

```markdown
# MAUDE Signal Report: <CODE> (<generic device name>)

**Recent period:** <start> to <end> · **Prior period:** <start> to <end>
**Data cutoff:** <date and why the window ends there> · **Source:** FDA MAUDE via NyquistAI · **Generated:** <today>

## Summary
<3–5 sentences: overall volume change, then the signals that need attention in priority order, and whether they're field-wide or concentrated in one manufacturer.>

## Deaths and serious injuries
<Death counts in both periods; how many recent deaths are plausibly device-related, unrelated/unknown, or miscoded, with a one-line paraphrase and link for each; what drives any change in injuries.>

## Signals needing attention
<Numbered, ranked list of 3–7 signals. For each: numbers (prior → recent, % change, share change), what the reports show, manufacturer concentration with exact counts, and a plain judgment (real shift / one firm's reporting / likely miscoding / too small to call).>

## Event types
<Table from the script, including decreases worth noting for context.>

## Device problems
### Increased more than 20%
<Table of the top ~15 by absolute increase; remaining increases in one compact line each for non-low and low counts.>
### New in the recent period
<Terms with 5+ reports named with counts; low-count terms in one compact sentence.>

## Patient problems
<Same layout as device problems.>

## Example reports
<Table: report number, date received, manufacturer, one-line paraphrase, link.>

## Limitations
<Specific to this data: MAUDE is passive and under-reports; reports aren't confirmed causes; counts are reports, not patients; batch filings and coding changes; incomplete recent data; low counts are noisy; how manufacturer counts were obtained.>

## Method
<Windows, thresholds, that counts come from full-period aggregations, whether any list hit the 100-term limit, how signals were investigated.>
```

Paraphrase narratives rather than pasting them. Don't call anything a confirmed safety issue: this is signal detection, and the report presents candidates for investigation, with the evidence for and against each.
