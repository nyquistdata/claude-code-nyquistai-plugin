---
name: "device-risk-analysis"
description: Risk and hazard analysis for a medical device product code, built from FDA MAUDE adverse event data, recalls and cleared/approved devices pulled through the NyquistAI connector, delivered as a Markdown report with a trend summary and an ISO 14971-style hazard table. Use this skill whenever the user gives a 3-letter FDA product code (e.g. DZE, LLZ, NIQ) and wants a risk analysis, hazard analysis, adverse event review, MAUDE review, post-market surveillance summary, complaint trending, or input for a risk management file, even if they don't say "hazard analysis" explicitly. Also use it when someone asks "what are the main hazards for X devices", "what goes wrong with devices under product code X", or wants the known failure modes and harms of a device type.
compatibility: Requires the NyquistAI connector (usfda_maude_search, usfda_recall_search, usfda_device_search). Load them with tool_search if deferred.
---

# Device Risk / Hazard Analysis

Produce a post-market risk analysis for an FDA product code: what fails, what harms result, how often (relative to other reports), how it trends, and how it maps to hazards. The reader is usually a regulatory, quality or R&D person building or updating a risk management file, so be precise, cite sources, and be honest about what MAUDE data can and cannot show.

## Inputs

- **Product code** (required): a 3-letter FDA product code. Uppercase it. If the user gives a device name instead, use `usfda_device_search` with the name as the query, show the likely product codes, and ask which one to use.
- **Time window** (optional): default is the past 3 years ending today. Use the user's window if they give one (e.g. "last 2 years").

## Step 1: Load the tools

If the NyquistAI tools aren't loaded, call `tool_search` with a query like "NyquistAI MAUDE recall device" to load `usfda_maude_search`, `usfda_recall_search` and `usfda_device_search`. All three take a single `request` object.

## Step 2: Pull the data

The responses can be large, so keep `size` small; the statistics come from aggregations, not the returned rows.

1. **Adverse event overview** — `usfda_maude_search` with `query: ""`, `product_code`, `date_received_from` / `date_received_to` (ISO datetimes), `size: 5`, `sort_by: "date_received"`. The `aggregations` (device_problem, patient_problem, event_type, received_by_year) cover *all* matching reports, not just the returned page, so they are the basis for every count in the report. `total_count` is the total number of reports. Never page through all records.
2. **Device context** — `usfda_device_search` with `query: ""`, `product_code`, `size: 10`, `sort_by: "decision_date"`. Gives the classification name, device class, submission type, specialty, and current manufacturers. Use its aggregations for device counts, submission types and average review days.
3. **Recalls** — `usfda_recall_search` with `query: ""`, `product_code`, `date_initiated_from` / `date_initiated_to` for the same window, `size: 25`. Note recall class (1 is most serious), reason, root cause, firm and status. If there are more than 25, use the aggregations (root cause, firm, year) for counts and summarize the most serious ones.
   - **If the window has zero recalls**, run the recall search again with no dates and `size: 3`, `sort_by: "date_initiated"`. This tells "no recalls recently" apart from "no recall data for this code" and gives the date and theme of the most recent one.

If the adverse event search returns zero reports, say so, check the product code with the device search, and still produce a short report from device and recall data.

## Step 3: Read narratives

Counts show *what* is reported; narratives show *how* the harm happens, which is what a hazard table needs. Narratives come back only with `show_details: true`, and many are null or boilerplate.

**Top failure modes.** For the top 3–5 device problems (skip generic codes like "Adverse Event Without Identified Device or Use Problem", "Insufficient Information", "Appropriate Term/Code Not Available"), call `usfda_maude_search` with `query` set to a few words describing the problem, the same `product_code` and dates, `show_details: true`, `size: 3–5`, `sort_by: "_score"`. Relevance sorting surfaces reports with real narratives; date sorting tends to return recent batch filings with no text. Keyword matching is loose, so the `total_count` of these searches is not a valid count for the problem; always take counts from the Step 2 aggregations.

**Deaths.** If the overview shows any deaths, call `usfda_maude_search` with `event_type: "Death"`, `query: ""`, the same `product_code` and dates, `show_details: true`, `size: 10`, `sort_by: "date_received"`. With this filter, the aggregations describe only the death reports, which gives you a death profile directly:

- **Share with no identified device problem** ("Adverse Event Without Identified Device or Use Problem"), which shows how much of the mortality is attributed to patient condition or procedure rather than a device failure.
- **Device problems that appear in deaths**: use these counts in the hazard table's Evidence column (e.g. "15 deaths") and to decide which hazards get S5.
- **Patient problems among deaths**: the causes of death as coded.

If there are 10 or fewer deaths, you have them all; read every one. If there are more, read the returned ones, and for the top 2–3 specific device problems that appear in deaths (skip the generic codes), run one more call each with `event_type: "Death"`, `query` set to that problem, `size: 3` to see how it led to death.

Check whether each death narrative actually describes a patient death. Some manufacturers miscode implant loss or malfunctions as deaths; if the death reports don't describe deaths, say so and don't assign S5 on that basis.

**Injuries when they are few.** When injuries are a small share of reports (e.g. software, where most reports are malfunctions), do the same with `event_type: "Injury"` to see what the injuries actually are; low-count but serious patterns (such as a missed diagnosis) are easy to miss in the overall aggregations.

**Duplicates.** One event can produce several reports: one per implanted unit (e.g. three stents), or the same event filed under two report numbers. When narratives are identical, note it and say counts overstate distinct events.

Keep notes on the hazardous situation, harm, and any stated cause or manufacturer conclusion for each mode. Record the report numbers and `official_url` of the examples you rely on so they can be cited.

## Step 4: Analyze

Work out, from the aggregations:

- Event type split (death, injury, malfunction, other) with percentages. Compute percentages with code rather than by hand.
- Top device problems and top patient problems with counts and percent of total.
- Year-by-year trend. The first and last years of the window are partial; mark them, compare full years, and annualize the current year if useful (say so).
- Reporting concentration: whether one manufacturer or brand dominates the sampled reports, files same-day batches with no narrative, or says it is reporting "out of caution" during a risk-file update or CAPA. A sudden jump in volume is often one firm's reporting decision, not a field-wide change. Name it when the evidence supports it.
- Links between device problems, patient problems and recalls (e.g. a recall root cause that matches a top failure mode, or a recall theme that MAUDE barely shows).

**Recalls can be the primary signal.** For software, and for codes where one generic failure dominates MAUDE (e.g. dental implants), recalls often reveal hazards MAUDE under-represents, because defects get caught and recalled before harm is reported. Give those hazards a row in the table even if their MAUDE frequency is Rare, and say the evidence is the recall record.

Then build the hazard table. For each significant hazard:

- **Hazard**: the source of potential harm (e.g. stent dislodgement from the delivery system, wrong-patient data association).
- **Hazardous situation**: the circumstances in which someone is exposed.
- **Harm**: the clinical outcome, from patient problems and narratives.
- **Severity** (justify briefly; for software, rate the potential clinical consequence since most reports describe no harm):
  - S5 Catastrophic: death
  - S4 Critical: permanent impairment or life-threatening injury
  - S3 Serious: injury needing medical or surgical intervention (e.g. revision, explant, retrieval)
  - S2 Minor: temporary injury or impairment not needing intervention
  - S1 Negligible: inconvenience or no injury
- **Relative frequency**: High (>10% of reports), Medium (1–10%), Low (0.1–1%), Rare (<0.1%). This is the share of *reports*, not a probability of occurrence, because MAUDE has no denominator (units sold or procedures). Say this in the table notes.
- **Evidence**: counts (including deaths linked to this problem, from the death profile) plus 1–2 cited example reports or recall numbers.
- **Possible controls / follow-up**: risk controls a manufacturer might consider or questions worth investigating, framed as suggestions, not conclusions. Cite relevant standards where natural (e.g. ISO 14801 fatigue testing, ISO 11607 packaging, ISO 10993 biocompatibility, FDA cybersecurity guidance).

Aim for roughly 8–11 hazards; merge near-duplicates rather than padding.

## Step 5: Write the report

Save the report as `<PRODUCT_CODE>_risk_analysis_<YYYY-MM-DD>.md` in `/mnt/user-data/outputs/` and present it with `present_files` (if no file tools exist, give the Markdown in the reply). Use this structure:

```markdown
# Risk / Hazard Analysis: Product Code <CODE> — <Device classification name>

**Data window:** <from> to <to> · **Source:** FDA MAUDE, recall and device databases via NyquistAI · **Generated:** <date>

## Executive summary
3–5 sentences: volume and event-type mix, dominant failure modes and harms, most serious findings (deaths, Class 1 recalls, recall themes), notable trend, and the main caveat.

## Device context
Classification, device class, submission pathway, medical specialty, number of cleared/approved devices, average review time, key manufacturers.

## Adverse event overview
- Event type table (type, count, %)
- Reports by year table, partial years marked, with one or two sentences on the trend

## Trend summary
### Top device problems
Table: problem, count, % of reports (top ~10–12).
### Top patient problems
Table: problem, count, % of reports.
### Deaths and serious injuries
Include when there are deaths (or few, notable injuries). A short table of device problems and patient problems among death reports (count, % of deaths), the share with no identified device problem, and 2–4 sentences on what the narratives describe, including any miscoded deaths or duplicates.
### Patterns and observations
Short bolded-lead paragraphs: what the failure modes look like in the narratives, how they connect to harms, reporting concentration and artifacts, duplicates.

## Recalls
Table: recall number (linked), date, firm, product, reason, root cause. Group by theme when there are many. Then 1–2 sentences linking recalls to adverse event patterns. If none in the window, say so and give the all-time count and most recent recall.

## Hazard analysis
Table with columns: ID, Hazard, Hazardous situation, Harm, Severity, Relative frequency, Evidence, Possible controls / follow-up.
Notes under the table: severity scale, frequency definitions and the no-denominator caveat, plus any note on miscoded deaths.

## Limitations
MAUDE is passive surveillance: reports may be incomplete, unverified or duplicated; volume depends on each manufacturer's reporting practice; counts can't establish incidence or causation; problem codes are reporter-assigned and overlap; example narratives come from loose keyword searches and illustrate rather than represent. Add anything specific to this code.

## Sources
Links to the example reports and recall pages cited.
```

Keep the prose tight and the numbers exact. Cite every example report by number with its link, and double-check that MAUDE links use the `cfMAUDE/detail.cfm?mdrfoi__id=` form and recall links the `cfRES/res.cfm?id=` form from the tool output. In the chat reply, give a 2–3 sentence summary of the headline findings rather than repeating the report.
