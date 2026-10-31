# Pilot validation before the jury demo

This is an execution checklist, not evidence of measured benefits or a prize probability.

## Live model gate

1. Set `LQ_MODEL_API_KEY` locally. Keep it out of chat, Git and screenshots. Confirm `LQ_MODEL_ID` against the Meta account.
2. In `backend`, run `..\\.venv\\Scripts\\python.exe -m app.verify_meta --probe --output ..\\private\\meta_probe.json` on Windows, or `../.venv/bin/python -m app.verify_meta --probe --output ../private/meta_probe.json` on Linux.
3. A successful probe confirms account access only. It does not validate grounded recommendations. Restart the API and worker after changing `.env`.
4. Import the source pack as drafts, review a small group of applicable criteria, and obtain independent approval and publication.
5. Run a real analysis from one of the author's nine assessments. Confirm completed status, actual model, usage and sources. Read every recommendation against the original reference. Save the printable report.

## Expert review

Use at least five findings across several criteria, including a partial answer, a missing observation, an insufficient-source case and a source withdrawn after an analysis request. Record whether each recommendation is supported by its citation, useful for the laboratory, correctly scoped and free of invented evidence or causes. Record corrections rather than hiding failures. `docs/PILOT_EVALUATION.csv` contains empty rows for actual measurements.

Compare manual and assisted time for the same task: prepare a reviewed, acceptable action plan. Include review and corrections in assisted time. Separate model latency from the total task duration. Report the individual cases, sample size and mean only after collecting observations. Do not infer national or clinical impact from five cases.

## Jury demo gate

- Confirm the current local installation still contains the author's nine imported assessments. The cloud build cannot inspect that local database.
- Use authorized, anonymized data. This release does not automatically anonymize audit comments.
- Show an assessment, readiness checks, applicable sources, a real completed Meta result and an action with owner and due date.
- Explain source verification and independent review. Do not present a test provider, pre-written recommendation or synthetic dataset as live inference or real pilot evidence.
- Rehearse the six-slide English pitch and the application transition. Target four minutes. Keep a recording of an actual successful run as a connectivity fallback.
- Confirm the portal's current duration and submission fields. Preserve Git history and disclose work that predates the eligible event period.
- Submit only claims supported by the actual run and expert review. The draft deck explicitly marks live validation as pending until evidence exists.

## Current limits

Live Meta access and expert validation remain pending the author's key and participation. The original ODK credentials and nine-submission database are not available in this environment. PostgreSQL, Docker, Windows execution and institutional deployment need environment-specific validation. These are not completed merely because contract tests pass.
