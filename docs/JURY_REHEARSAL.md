# Jury rehearsal — fictional case, real Meta response

This guide prepares the recording without opening the existing laboratory
database. Keep the normal `.env`, database and evidence files in place. Use a
separate checkout of the candidate for the recording, with dependencies
installed and the Meta settings configured locally. Never copy a database,
evidence directory or `.env` into the public repository.

## Prepare the isolated workspace

In `frontend`, run `npm run typecheck` and `npm run build`. At the project root:

```powershell
.\scripts\start-jury-demo.ps1 -RunMeta
```

The command creates a new directory under `.jury-demo/`, applies migrations
to a new SQLite database and imports a fictional assessment with two retained
revisions. It publishes an explicitly fictional training procedure through
separate author and reviewer accounts. Only this fictional case is sent to
`https://api.meta.ai/v1/responses`. ODK and email are disabled in the recording
workspace. A failed Meta run stops preparation; it is never replaced with a
simulated response. Running without `-RunMeta` prepares only an offline case
and is insufficient for the final AI demonstration.

API, worker and interface run on ports 18001 and 13300. Processes start hidden,
with logs and their PIDs in the new directory. Open http://127.0.0.1:13300.
The script checks readiness before reporting success. The shell's original
environment variables are restored after starting the child processes.

The demo-only password is `Fictional-recording-only-2026!`. Accounts:

| Account | Purpose |
| --- | --- |
| `admin@labquality.local` | Review the model proposal and approve the example action. |
| `qualidade@labquality.local` | Own the action, attach the fictional evidence and request verification. |
| `verificador@labquality.local` | Review the evidence and record the independent example verification. |

The local `demo-receipt.json` identifies the assessment and genuine completed
run. `genuine-meta-response.json` is created only after a real successful call.
Neither file contains the API key. The sample `fictional-evidence.txt` is a
training artifact; it establishes no real laboratory compliance.

## Rehearse the complete case

1. Set the interface to English. In **Assessments**, search for
   `PUBLIC-DEMO-REVIEW-001`. Open it, inspect finding 1.5 and expand
   **Source and revisions**. Show the two revisions; previous assessments for
   the same laboratory are available in the list. Scores remain provisional
   and are not the focus of this demonstration.
2. In **Quality copilot**, open the completed run from the receipt. Show
   `muse-spark-1.3`, status, duration, one proposal and the supporting source.
   The model's draft may be in Portuguese even with the interface in English;
   explain it in the English narration. Do not claim an unimplemented output
   language selector.
3. Select **Review and create action**. Review the content yourself, use a
   clear English title such as *Review obsolete document copies*, assign the
   quality account and choose a deadline. Saving creates a proposal; it does
   not automatically approve the action. Approve it as the administrator.
4. Sign out and sign in as the quality account. Open **Improvement plans**,
   start the action, attach `fictional-evidence.txt`, add a training note and
   request verification. The evidence illustrates the workflow only.
5. Sign out and sign in as the verifier. Inspect the evidence, select it and
   record the example effectiveness review. Confirm closure and the named
   verifier. Never claim this demonstration certifies a real laboratory.

Record genuine states and genuine user decisions. Prepared records are
allowed, but identify the dataset as fictional and the model response as
precomputed when opening an existing run. Do not portray an edited wait as
instantaneous inference. Do not use the transport stub from automated tests
in a public demonstration.

## Film and submission gates

Target 2:50–2:55, maximum 3:00, with English narration. Spend most of the time
inside the application. Keep credentials, configuration screens and private
notifications out of frame. Review the exported video for legibility, sound,
duration and accidental disclosures. Confirm both the video URL and the
commit URL in a signed-out browser. Library download links and local paths
are not a substitute for a video URL accessible to the jury.

The authenticated submission form must confirm the required fields and the
already-selected track. Describe the code that began on 23 October and the
later additions honestly; Git history documents changes but does not by
itself establish compliance with the accepted event rules.

Internal target: **4 November 2026, 18:00 Africa/Maputo**. Official deadline
in the organizer's 3 November email: **5 November, 04:00 Africa/Maputo**.
Keep the platform confirmation and a copy of the answers. Until that exists,
the project remains **not submitted**.
