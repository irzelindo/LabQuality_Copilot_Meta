# Third-party materials

The MIT licence in `LICENSE` covers the original LabQuality Copilot software
and original project documentation. It does not relicense external standards,
checklists, assessment instruments, supplied data, third-party packages, names
or trademarks.

## SLIPTA and the supplied assessment instrument

The project refers to the WHO SLIPTA Checklist Version 3, dated 22 December
2023, published through the African Society for Laboratory Medicine (ASLM):

- https://aslm.org/resource/whos-stepwise-laboratory-quality-improvement-process-towards-accreditation-slipta-checklist/
- https://aslm.org/wp-content/uploads/2019/12/SLIPTA-Checklist-V3-22-Dec-2023.pdf

The criterion mapping and pilot examples were prepared from an XLSForm
supplied by the project owner. Criterion titles, source references and any
third-party text retain their original ownership and applicable terms. This
repository does not grant a new licence to WHO, ASLM, ISO or CLSI materials.

In particular, reference-related content in `backend/app/slipta_pilot.json`,
`backend/samples/slipta_sources/`, the generated pilot assessment examples and
the corresponding files in `frontend/public/demo/` must be distinguished from
the original software. The section documents provide evidence-checking
questions for review. They are not local laboratory procedures, proof of
implementation or an official compliance decision.

The full official checklist and the owner's original XLSForm are not bundled
in this code snapshot. Obtain source documents from their authorized source
and check their applicable terms before redistribution or institutional use.
References to ISO 15189:2022 and CLSI do not include or grant rights to those
standards. No institutional endorsement is implied.

## Software dependencies and model services

Dependencies retain their own licences. Their versions are recorded in
`backend/requirements.lock` and `frontend/package-lock.json`; installed
dependency directories are not part of the source distribution. Include any
required dependency notices when distributing a built application.

Meta model names identify the external service used by the adapter. The MIT
licence does not grant rights to model weights, API access or service credits.
Use Meta services under the applicable account and service terms.

## Private information

The application does not license or authorize publication of laboratory data,
patient information, uploaded evidence, account credentials or local databases.
Public demonstrations must use fictional data or material authorized for public
disclosure.
