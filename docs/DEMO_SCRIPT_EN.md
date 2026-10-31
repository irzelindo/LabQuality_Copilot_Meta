# LabQuality Copilot: four-minute jury presentation

Six slides. Use the speaker notes in the editable presentation. The script below keeps the argument concise and gives the app demonstration most of the time.

## 0:00-0:25 - Introduction

I am Irzelindo Salvador, an informatics specialist working with laboratory systems in Mozambique. LabQuality Copilot helps laboratory teams turn assessment findings into improvement plans supported by traceable evidence.

## 0:25-0:55 - The problem

An audit identifies gaps. The quality team still has to find the relevant requirements, prepare appropriate actions, assign responsibility and verify the result. Our project connects those steps in one workflow.

## 0:55-1:30 - The solution

We import an ODK assessment and keep its history. The application calculates the scores. Meta receives selected findings and the published references that apply to them. It proposes action steps with exact source quotes. A person reviews the proposal before creating an action. Another authorized person checks the evidence before closure.

## 1:30-2:10 - What Meta adds

The model uses the finding, the auditor's observations and relevant source text to draft an action plan in Portuguese or English. The application checks the response structure, source quotations and criterion links. A qualified person still checks whether each recommendation makes sense. The model cannot change scores or award accreditation.

## 2:10-3:15 - Product demonstration

Open a real authorized, anonymized assessment and say:

Here is the assessment and its recorded findings. Before calling Meta, the application shows whether the selected findings have published sources. I will select a small group and run the analysis.

After a real completed run, say:

This proposal includes its justification, the source quotation and a completion criterion. The reviewer can read the source, correct the proposal and create an action with an owner and a due date. The team can then attach evidence and request independent verification.

If live Meta inference is still unavailable, use this truthful alternative:

The preparation workflow and evidence controls are implemented. Live model validation is pending API access. I will show the working preparation and action workflow today. We will validate the actual recommendations before claiming a completed AI pilot.

## 3:15-3:55 - Evidence and next step

We prepared 151 criterion-linked references from the supplied SLIPTA files. Nine ODK assessments have been imported in the author's local installation. The next validation is a live Meta run, expert review of the recommendations and a measured comparison of action-planning time. Our aim is to make laboratory improvement work easier to carry out and easier to verify.

## Short answers for the jury

**Why Meta?** The integration uses Meta's Responses API for structured, multilingual improvement proposals grounded in selected laboratory findings and published source text. Cite the actual model and run receipt after live validation.

**How do you handle hallucinations?** The application restricts source access, verifies quoted text and criterion links, rejects unsupported references and requires human review. These controls reduce identifiable failure modes. They do not prove semantic accuracy.

**Does this award SLIPTA stars?** No. The supplied source files contain inconsistent weights. The prototype preserves instrument versions and reports pilot results without awarding official recognition or accreditation.

**What evidence of impact do you have?** The author has completed local import of nine assessments. Time savings and recommendation quality have not yet been measured. Describe actual measurements only after completing the pilot worksheet.

**What was built during the event?** Use the preserved Git history and branch comparison. The baseline project began before the event. Do not attribute earlier work to the competition window or assume eligibility without checking the event instructions.

**Can the jury try it?** Offer an authorized installation with anonymized data. Do not expose a public demo with real records or credentials. There is no hosted public deployment in this delivery.
