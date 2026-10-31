# Validation record - 31 October 2026

The project was checked in an isolated Linux environment against the GitHub baseline. Real ODK records on the author's computer were neither accessed nor changed.

- Backend: 31 automated tests passed, including existing calculations, authorization, import revisions, action/evidence verification, readiness, reference import and independent approval, incomplete provider responses, source withdrawal, criterion aliases, conservative N/A handling, report scope and HTML escaping, source preparation and provenance.
- Frontend: TypeScript check and production build passed.
- Browser: 3 end-to-end tests passed, covering guided preparation on desktop/mobile, reference-pack preview/import with independent review, and the original action/evidence verification workflow.
- Original source preparation: 151 criterion-linked references, all with PDF text and page matches. PDF question weights sum to 365, declared total is 373, XLSForm weights sum to 364, and criterion 8.22 differs (XLSForm 2, PDF 3). See SLIPTA_SOURCE_REVIEW.md.
- Meta integration: contract-tested with a controlled transport. No live Meta call was made because the author has not yet supplied the key. No test output is presented in the application or deck as a real model run.
- Presentation: six-slide editable deck with speaker notes. Claims distinguish implemented controls, author-reported progress and pending validation.

To reproduce:

```bash
cd backend
../.venv/bin/python -m pytest -q
../.venv/bin/python -m alembic check
cd ../frontend
npm run typecheck
npm run build
npx playwright install chromium
npm run test:e2e
```

In the isolated environment, the default Playwright browser download failed. Browser checks used a separately installed Chromium executable via LQ_BROWSER_EXECUTABLE. This does not add a browser dependency to the application or change user installation requirements.

Known limits: no live account validation, no local nine-submission reconciliation, no expert recommendation scoring, no measured time savings, no Windows execution, and no Docker/PostgreSQL or SMTP deployment validation. Passing automated checks does not validate recommendations semantically or establish a probability of winning.
