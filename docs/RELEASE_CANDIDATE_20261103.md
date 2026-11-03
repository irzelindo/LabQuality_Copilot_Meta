# Hackathon release candidate — 3 November 2026

Base commit: `6f8dd57497b0928f961332cce17599bc7e3b4695` on
`feature/slipta-v3-scoring`. The candidate is the commit containing this file;
use its full GitHub commit URL in the submission. Changes are limited to the
demonstrable audit workflow, reference handling, licensing and rehearsal.
No production deployment or change to the existing installation is included.

## Changes

- MIT licence for the original software, with separate third-party notices.
- Prompt `quality-actions-v2`: conflicting applicable sources require a human
  decision instead of an unsupported choice between sources.
- Quote validation permits whitespace changes only, and restores the exact
  original source span before saving. Altered words, case and punctuation
  remain rejected. Citations must respect each finding's permitted sources.
- A fresh fictional rehearsal case with two revisions, source publication by
  a separate account, optional genuine Meta inference and separate storage.
- A Windows launcher with isolated database paths, disabled ODK/email,
  dedicated ports, readiness checks and recorded process IDs.

## Verification performed on this candidate

| Check | Result and practical limit |
| --- | --- |
| Backend | 58 tests passed across fresh processes per test module, using temporary databases and a socket-free ASGI test harness. |
| New quote regressions | Five cases: restore line wrapping; reject changed words, case, punctuation and an unauthorized source. Included in the 58. |
| Browser | Six existing scenarios passed using the built production frontend and actual ASGI API over an in-memory bridge, with a fresh fictional database per test. The upload scenario passed on a focused rerun after correcting the bridge's file handling. |
| TypeScript | `tsc --noEmit` passed. |
| Production build | `next build` exited successfully. The restricted Windows host emitted an EPERM warning while copying traced standalone files; normal networked deployment was not validated. |
| Demo preparation | Fresh database, two assessment revisions and independently published fictional source prepared successfully. |
| Windows launcher | PowerShell syntax passed. Process startup and readiness need verification on the user's Windows installation. |
| Genuine Meta call in this session | Attempted with only the new fictional case; blocked by the host network. No successful response was fabricated. |

The host blocks loopback connections. Its normal Windows asyncio self-pipe
could not start; tests used an external harness that polls thread notifications
without opening sockets. A whole-suite process also encountered a native
Windows access violation; running each module in a fresh process completed
the 58 checks. These are functional regression results, not a load test or a
confirmation that production deployment and live integrations work.

Only public source files matching the base snapshot were used to construct
the isolated candidate. Existing `.env`, the installed database and uploaded
evidence were not modified. The full checklist and the original XLSForm are
not redistributed under the software licence; consult `THIRD_PARTY_NOTICES.md`.

## Remaining delivery gates

1. Run `scripts/start-jury-demo.ps1 -RunMeta` in a separate installed checkout
   and confirm a genuine completed response with model and source visible.
2. Personally review one recommendation, create/approve an action, upload
   fictional evidence and verify it using the verifier account.
3. Record and review an English video of no more than three minutes.
4. Publish the video and test its URL and the code permalink without a login.
5. Confirm the authenticated form's fields and the already-selected track.
6. Review the actual accepted rules and disclose pre-existing components.
   Project preparation began on 23 October, before the advertised kickoff;
   Git history is available to distinguish later work. This candidate does
   not make an eligibility determination.
7. Submit, retain the confirmation and save the final answers. Until the
   platform confirms receipt, the status is **not submitted**.

Internal target: 4 November, 18:00 Africa/Maputo. The organizer's 3 November
email specifies 4 November, 21:00 GMT−5, equivalent to 5 November, 04:00 Maputo.
No prize probability, autonomous audit accuracy or measured time saving is
claimed by this release.
