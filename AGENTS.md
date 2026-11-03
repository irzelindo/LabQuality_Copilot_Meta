# LabQuality Copilot

Read README.md and docs/IMPLEMENTATION_STATUS.md before making changes.

- Monorepo: backend/app (FastAPI), frontend/src (Next.js), scripts and deployment.
- Preserve organization and laboratory authorization in every query and every job.
- Assessment identity is organization + source + external_id. Reimports are idempotent; corrections create immutable revisions.
- Do not change scoring in the model layer. The demo rubric is fictional and has no official SLIPTA classification.
- AI must use a real server-side provider, published authorized sources, exact citations and human review. Never simulate successful inference or fabricate benefits.
- Keep model, ODK, SMTP and database secrets out of frontend code, logs and version control.
- Any schema change needs a new Alembic migration and relevant regression tests.
- Run backend tests, frontend typecheck and build. Use browser tests for modified user flows.
- The owner authorized committing and pushing validated feature branches to `irzelindo/LabQuality_Copilot_Meta` on 26/10/2026. Keep `main` stable and sync through feature branches; a pull request is not required. Do not deploy or create worktrees without a request.
- Public presentation must identify implemented, unverified and planned capabilities accurately.

Local commands (from the relevant directory):

    python -m pytest -q
    npm run typecheck
    npm run build

The Windows target is D:\irzelindo\Documentos Pessoais\Candidaturas\Meta Hackathon\hackathon.
