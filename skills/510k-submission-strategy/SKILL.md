---
name: 510k-submission-strategy
description: Develop comprehensive 510(k) submission strategy for medical devices including predicate device analysis, product code selection, testing requirements, and Pre-Submission planning. Use when user mentions 510(k), predicate devices, substantial equivalence, Q-Sub, or medical device clearance strategy.
---

# 510(k) Submission Strategy Development

## Purpose
Guide the development of a complete 510(k) submission strategy by identifying appropriate predicate devices, determining product codes, defining testing requirements, and preparing Pre-Submission objectives.

## When to Use This Skill
Use this skill when the user needs to develop a 510(k) submission strategy or pathway for a medical device.

## Workflow: DO NOT Skip Any Step

### Step 1: Gather Initial Information
**MANDATORY: Ask these questions before proceeding:**

1. What are the **Indications for Use** for your device?
2. What is the device description?

**STOP HERE until you receive this information. Do not proceed to Step 2 without the Indications for Use.**

---

### Step 2: Predicate Device Search
**Objective:** Identify FDA-cleared devices that could serve as predicates.

**Instructions:**
1. Search the FDA 510(k) database for devices with similar indications for use
2. Search by keywords from the indications, device type, and intended use
3. **CRITICAL:** When presenting results, ALWAYS include the exact K number (e.g., K123456) for each device
4. Identify 3-5 potential predicate candidates
5. Present candidates in a table format:
   - K Number (MANDATORY)
   - Device Name
   - Manufacturer
   - Product Code
   - Clearance Date
   - Brief Description

**Output Format:**
```
## Potential Predicate Devices

| K Number | Device Name | Manufacturer | Product Code | Date | Description |
|----------|-------------|--------------|--------------|------|-------------|
| K123456  | [Name]      | [Mfg]        | XXX          | [Date] | [Brief desc] |
```

---

### Step 3: Download and Analyze Predicate Summaries
**Objective:** Review detailed information about predicate candidates.

**Instructions:**
1. For each identified predicate device, locate and download the 510(k) Summary PDF from the FDA database
2. Use web_fetch or appropriate tools to retrieve these documents
3. Read each PDF summary 
4. Extract key information:
   - Indications for Use statement
   - Technological characteristics
   - Performance testing conducted
   - Product code used
5. Compare similarities and differences with the new device

**Analysis Format:**
```
## Predicate Analysis: [K Number]

**Device:** [Name]
**Indications for Use:** [Copy from summary]
**Key Technologies:** [List]
**Testing Performed:** [Summarize]
**Product Code:** [Code]
**Similarity to New Device:** [Assess]
**Potential as Predicate:** [Strong/Moderate/Weak - with rationale]
```

---

### Step 4: Testing Requirements Analysis
**Objective:** Define required testing based on predicate comparisons and FDA guidance.

**Instructions:**
1. Based on the predicate summaries and FDA guidance, compile a comprehensive testing plan
2. Categorize tests by type:
   - **Biocompatibility Testing** (per ISO 10993 series)
   - **Performance Testing** (mechanical, functional)
   - **Safety Testing** (electrical, thermal, chemical)
   - **Clinical Testing** (if required)
   - **Software Verification & Validation** (if applicable)
   - **Sterilization Validation** (if applicable)
3. For each test, note:
   - Test purpose
   - Applicable standard
   - Why it's required (predicate comparison or guidance requirement)

**Output Format:**
```
## Required Testing Program

### Biocompatibility Testing
- ISO 10993-1: Biological Evaluation
  - Rationale: [Device contact type/duration]
  - Specific tests: [List per ISO 10993-1 matrix]

### Performance Testing
- [Test Name]: [Standard]
  - Rationale: [Why required]
  - Acceptance criteria: [From predicates/guidance]

[Continue for all categories...]
```

---

### Step 5: Pre-Submission (Q-Sub) Objectives
**Objective:** Formulate questions for FDA Pre-Submission meeting.

**Instructions:**
1. Based on all analysis above, identify areas of uncertainty or risk
2. Formulate specific questions for FDA feedback
3. Prioritize questions by importance
4. Group by topic area

**Output Format:**
```
## Recommended Pre-Submission (Q-Sub) Objectives

### Primary Objectives

1. **Predicate Device Acceptability**
   - Question: Does FDA agree that [K number] is an appropriate predicate for substantial equivalence?
   - Rationale: [Why this needs clarification]

2. **Product Code Confirmation**
   - Question: Does FDA agree with the proposed product code [XXX]?
   - Rationale: [Any ambiguity or concerns]

3. **Testing Protocol Agreement**
   - Question: Is the proposed testing protocol sufficient to demonstrate substantial equivalence?
   - Specifically regarding: [List any unique/novel tests]

### Secondary Objectives

4. **[Additional Question Topic]**
   - Question: [Specific question]
   - Rationale: [Why asking]

[Continue as needed...]
```

---

## Final Report Structure

After completing all 5 steps, compile a report with the following sections:
```
# 510(k) Submission Strategy Report
## [Device Name]

---

## Executive Summary
[2-3 paragraph overview of strategy]

---

## 1. Device Classification

**Medical speciality**
**Regulation Number**
**Product Code(s)**

## 2. Predicate Device Analysis
[Table and analysis from Steps 2-3]

**Recommended Primary Predicate:** [K number]
**Substantial Equivalence Rationale:** [Brief summary]

---

## 3. Required Testing Program
[Complete testing list from Step 4]

---

## 4. Pre-Submission Meeting Objectives
[Questions from Step 5]

---

## 5. Recommended Next Steps
1. [Action item]
2. [Action item]
3. [Action item]
```

---

## Important Notes

- **Always cite K numbers:** Every mention of a predicate device must include its K number
- **Download actual documents:** Always attempt to download and read the actual 510(k) summaries and guidance documents, don't rely on database descriptions alone
- **Stay current:** Use web search to find the most recent FDA guidance and database information
- **Document sources:** Include links to all FDA documents referenced
- **Markdown:** Produce the final report content using Markdown format. Don't use JS or other code to generate .docx files.

---

## Quality Checks Before Finalizing

Before presenting the final report, verify:
- [ ] Indications for Use are clearly stated
- [ ] All K numbers are exact and verified
- [ ] At least 3 predicate candidates analyzed
- [ ] Product code recommendation is justified
- [ ] Testing requirements are comprehensive and linked to standards
- [ ] Consensus standards are listed with recognition status
- [ ] Q-Sub objectives are specific and answerable
