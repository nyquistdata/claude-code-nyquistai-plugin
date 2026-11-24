---
name: "pma-submission-strategy"
description: Build an FDA PMA (Premarket Approval) submission strategy report for a Class III medical device, delivered as a Markdown file. Collects the device description and intended use first, then uses the NyquistAI connector to find precedent PMAs, classification, FDA guidance, similar clinical trials and post-market signals. Use this skill whenever the user mentions PMA, premarket approval, Class III device approval, modular PMA, PDP, IDE-to-PMA planning, SSED, advisory panel preparation, or wants a regulatory strategy or pathway plan for a high-risk or novel device, even if they don't say "PMA" explicitly. For 510(k) strategy use the 510(k) skill instead.
compatibility: Uses the NyquistAI connector (usfda_device_search, usfda_regulation_search, usfda_guidance_search, global_trial_search, usfda_recall_search, usfda_maude_search, usfda_warning_letter_search, usfda_inspection_citation_search). Load them with tool_search if deferred. web_search / web_fetch are used for current MDUFA goals, fees and reading SSED/guidance PDFs.
---

# PMA Submission Strategy

Produce a PMA submission strategy report a regulatory affairs lead could take into a planning meeting: which pathway and PMA type, what evidence FDA will expect, what precedent says, where the risks are, and what to do next. The reader is a regulatory, clinical or quality professional, so be precise, cite every FDA record you rely on, and keep clear which statements come from FDA data and which are your judgment.

## Step 1: Collect the device description and intended use (do this first)

The intended use drives classification, precedent, clinical endpoints and labeling, so nothing useful can be searched or written without it. Before any connector call, make sure you have:

**Required**
1. **Device description**: what it is, how it works (principle of operation), main components, materials that contact the patient, energy source, software, whether it is implanted or single-use.
2. **Intended use / indications for use**: the disease or condition, target population, anatomical site, clinical setting, and the claim (diagnose, treat, monitor, etc.).

**Helpful (ask in the same message, but don't block on them)**
- Development stage (concept, design freeze, feasibility data, pivotal-ready)
- Existing data: bench, animal, clinical (including OUS / CE-marked data)
- Known competitors or similar approved devices, and the product code if known
- Whether it contains a drug or biologic (combination product)
- Company size (small-business fee eligibility) and target submission date

If the user hasn't provided the required items, ask for them in one concise message and **stop until they reply**. If they uploaded a document (design spec, IFU draft, pitch deck), read it and extract the answers instead of asking again; confirm your summary of the intended use in one or two sentences before moving on. If the description is too vague to search (e.g. "a heart device"), ask one targeted follow-up rather than guessing.

## Step 2: Load the tools

If the NyquistAI tools aren't loaded, call `tool_search` with a query like "NyquistAI FDA device guidance regulation trial" to load them. Every NyquistAI tool takes a single `request` object.

Use the connector **when it adds evidence the user hasn't already given**. If the user supplied the product code, don't re-derive it; just confirm it. Keep `size` small (5–15) and rely on `aggregations` for counts, since responses can be large.

## Step 3: Classification and pathway check

1. **Find similar devices**: `usfda_device_search` with `query` set to 2–4 keywords from the intended use and technology (e.g. "transcatheter mitral valve repair"), `size: 15`. Read the `aggregations` for product code, device class and submission type.
2. **Precedent PMAs**: repeat with `submission_type: "PMA"` (and the product code once known), `sort_by: "decision_date"`. Record P numbers, device names, applicants, decision dates, `clinical_trial_flag`, `combination_product_flag` and `summary_pdf_link`.
3. **Pathway sanity check**: search the same product code with `submission_type: "510(K)"` and `"De Novo"`. If lower-risk pathways exist for the same code or a close one, say so plainly in the report: the PMA assumption may need challenging.
4. **Classification regulation**: `usfda_regulation_search` with the device type (e.g. "cardiac ablation catheter") to find the 21 CFR section and confirm Class III, and whether the regulation calls for PMA or the device is a post-amendments (not classified) Class III device.
5. **No precedent found**: try broader or alternative terms twice. If still nothing, treat the device as novel: note that De Novo may be possible if the risk can be shown to be moderate, and that a Pre-Sub or 513(g) request is the way to confirm classification.
6. **PMA supplements**: the NyquistAI device database lists original PMAs but not supplements, so new indications and new models approved by supplement (often the most relevant precedent) won't show up there. Run `web_search` for the indication plus "FDA approval" and for each key precedent device name plus the indication (e.g. "Onyx middle meningeal artery FDA approval"). Also check the PMA database page for each precedent: it lists supplement numbers. Add supplement approvals to the precedent table, marking their source (FDA record vs. company announcement) and tagging any detail not confirmed on an FDA page as **[To confirm]**.

### Check whether the device is already approved

Once precedents are found, compare the user's device description and indications for use against each precedent's SSED or database record. If they match an approved device verbatim or nearly so (same materials, same mechanism, same indication wording), **stop and ask the user before continuing**, in one short message that names the matching P number:

- Are they that device's sponsor (or do they have a right of reference to its data)? If so, the device is already approved and the work is a PMA supplement strategy, not an original PMA; adjust the report accordingly.
- Are they a new sponsor developing a similar device, or using the approved device's text as a test case? If so, proceed with an original-PMA strategy, and state this assumption prominently at the top of the report.

A match changes the whole strategy, so don't silently assume either answer.

## Step 4: Read precedent SSEDs

For the 2–4 most relevant precedent PMAs, read the Summary of Safety and Effectiveness Data (SSED). The SSED is usually the `summary_pdf_link` ending in "B.pdf"; "A.pdf" is the approval order and "D.pdf" is often the labeling.

`web_fetch` only opens URLs that appeared in a web search or fetch result, so fetching a `summary_pdf_link` straight from a NyquistAI result is rejected. First `web_search` for the PMA number plus "summary of safety and effectiveness" (e.g. "P250009 summary of safety and effectiveness"), then `web_fetch` the accessdata.fda.gov PDF link from the search results with PDF text extraction on. The approval order (A.pdf) is worth reading too when you need the exact post-approval study conditions.

From the SSED, extract: indications, pivotal study design (randomized vs single-arm, control, performance goal), primary safety and effectiveness endpoints, sample size, follow-up duration, key nonclinical tests, whether an advisory panel was held, and post-approval study conditions. This is the most valuable evidence in the report; FDA tends to expect a new device to clear at least the bar set by its predecessors. If a PDF won't load, say so and rely on the database record.

## Step 5: Guidance and standards

Use `usfda_guidance_search` for:
- Device-specific guidance (query with the device type and product area)
- Cross-cutting guidance relevant to this device; pick what applies rather than listing everything: PMA benefit-risk factors, IDE / clinical study design, Breakthrough Devices, modular PMA, software (content of premarket submissions), cybersecurity, biocompatibility (ISO 10993-1 use), human factors, sterility, OUS clinical data, Pre-Submission program.

Sort by `issue_date` when you need the latest version, and record title, issue date and `fda_url`. Mention whether guidance is draft or final when the record shows it. Don't fabricate standard numbers; list consensus standards only when the guidance, SSEDs or your knowledge clearly ties them to this device type, and recommend checking FDA's recognized-standards database for current recognition status.

## Step 6: Clinical landscape

`global_trial_search` with `intervention_type: "Device"` and keywords from the indication, `size: 15`. Look at trials by competitors or for precedent devices: design, endpoints, enrollment, countries, status. Use these to support the proposed pivotal design and sample size range, and to flag where the field has moved (e.g. recent trials using a randomized control where older PMAs used a performance goal).

## Step 7: Post-market and compliance signals (when relevant)

Run these when there is a known product code, and keep them light since the report is about strategy, not a full risk analysis:
- `usfda_maude_search` (`query: ""`, product code, last 3 years, `size: 5`): use the `aggregations` for top device and patient problems and event-type split. These inform the risk register, labeling and likely FDA review questions.
- `usfda_recall_search` (product code, last 5 years): recall themes and root causes worth designing out.
- Optionally `usfda_warning_letter_search` or `usfda_inspection_citation_search` for common QMSR/design-control findings in this device area, to sharpen preapproval inspection readiness.

## Step 8: Current program facts

Use `web_search` for anything that changes year to year rather than stating it from memory: current MDUFA review goals for original PMAs, current fiscal-year PMA user fee and small-business reduction, and the status of FDA's electronic submission template for PMAs. Cite the FDA page.

## Step 9: Write the report

Read `references/report-template.md` and follow its section structure. Then:

- Save the report as Markdown to `/mnt/user-data/outputs/<device-short-name>-pma-strategy.md` (lowercase, hyphenated) and share it with `present_files`. Keep the chat message short: two or three sentences on the recommended pathway and the top risks.
- Write in prose with tables where the template calls for them. Every precedent device gets its P number and a link; every guidance gets its title, date and link.
- Cite sources in the file as plain Markdown links (e.g. `[P250009 SSED](https://...)`) or "per the SSED"-style attributions. Never put chat citation markup (such as `<cite>` tags or search-result indices) in the report file: it doesn't render and the reader sees raw tags. Chat-style citations belong only in the chat message.
- Paraphrase SSEDs and other sources in your own words, and keep any direct quote short.
- Label judgment calls as recommendations and evidence gaps as **[Assumption]** or **[To confirm]**, so the reader can tell what's sourced.
- State the data pull date near the top.
- End with a one-line note that the report supports, and doesn't replace, review by qualified regulatory counsel and FDA feedback through a Pre-Submission.

## Quality checks before sharing

- Intended use is stated exactly as the user gave or confirmed it
- Pathway choice (PMA vs De Novo vs 510(k)) is justified, including evidence against PMA if any was found
- Every P number, product code and CFR section came from a tool result, not memory
- At least two precedent SSEDs were read, or the report says why not
- Clinical strategy has a concrete proposed design, endpoints and an explained sample-size basis (or a clear statement of what's needed to set it)
- Q-Sub questions are specific enough for FDA to answer yes/no or with a clear recommendation
- The 21 CFR 814.20 content map shows status and owner for each element
- Time-sensitive facts (MDUFA goals, fees) are cited from a current FDA source
- The device was checked against approved precedents, and any near-identical match was raised with the user and the answer reflected at the top of the report
- PMA supplement approvals for the indication were searched for, not just original PMAs
- The report file contains no `<cite>` tags or search-result indices (run `grep -n "<cite" <file>` before sharing)
