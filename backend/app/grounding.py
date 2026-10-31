"""Deterministic selection of authorized evidence before any model call."""
import re
from fastapi import HTTPException
from sqlalchemy import select
from .models import AssessmentRoot, Document, Finding, Instrument
from .operations import documents_for
from .services import score

MAX_FINDINGS = 5


def criterion_key(value: str) -> str:
    """Accept explicit SLIPTA field aliases, never fuzzy-match unrelated criteria."""
    match = re.fullmatch(r"p2_s\d+_(\d+)_(\d+)(?:_([a-z]))?(?:_calculate)?", value)
    if match:
        return ".".join(x for x in match.groups() if x)
    return value.strip().lower()


def source_applies(source, code):
    return not source.criterion_codes or criterion_key(code) in {criterion_key(c) for c in source.criterion_codes}


def published_sources(db, user, laboratory_id):
    return list(db.scalars(documents_for(db, user).where(
        Document.status == "published",
        (Document.laboratory_id.is_(None)) | (Document.laboratory_id == laboratory_id)
    ).order_by(Document.code, Document.revision.desc())))


def prepare_context(db, user, assessment, finding_ids=None):
    findings = list(db.scalars(select(Finding).where(
        Finding.organization_id == user.organization_id,
        Finding.assessment_id == assessment.id,
        Finding.laboratory_id == assessment.laboratory_id
    ).order_by(Finding.critical.desc(), Finding.criterion_code, Finding.id)))
    ids = finding_ids or []
    if len(ids) > MAX_FINDINGS or len(ids) != len(set(ids)):
        raise HTTPException(422, "Seleccione até cinco achados distintos por análise.")
    if set(ids) - {f.id for f in findings}:
        raise HTTPException(422, "Os achados seleccionados não pertencem a esta avaliação.")
    chosen = [f for f in findings if f.id in ids] if ids else findings[:MAX_FINDINGS]
    sources = [s for s in published_sources(db, user, assessment.laboratory_id) if s.content.strip()]
    selected_sources = {}
    coverage = {}
    for finding in chosen:
        applicable = [s for s in sources if source_applies(s, finding.criterion_code)]
        # Specific criteria take precedence over organization-wide general procedures.
        applicable.sort(key=lambda s: (not bool(s.criterion_codes), s.code))
        coverage[finding.id] = [s.id for s in applicable[:2]]
        for source in applicable[:2]:
            selected_sources[source.id] = source
    instrument = db.get(Instrument, assessment.instrument_id)
    criteria = {c["code"]: c for c in instrument.criteria}
    context = {
        "assessment_id": assessment.id,
        "instrument": {"code": instrument.code, "version": instrument.version,
                       "scoring_rule": instrument.scoring_rule},
        "scoring": score(assessment, instrument),
        "findings": [{
            "id": f.id, "criterion_code": f.criterion_code,
            "description": f.title, "critical": f.critical,
            "score": assessment.answers.get(f.criterion_code, {}).get("value"),
            "maximum": criteria.get(f.criterion_code, {}).get("maximum"),
            "auditor_comment": assessment.answers.get(f.criterion_code, {}).get("comment", "")[:2000]
        } for f in chosen],
        "sources": [{
            "id": d.id, "code": d.code, "revision": d.revision, "title": d.title,
            "criterion_codes": d.criterion_codes, "content": d.content[:12000]
        } for d in selected_sources.values()]
    }
    root = db.get(AssessmentRoot, assessment.root_id)
    return context, findings, coverage, root.head_revision == assessment.revision


def readiness(db, user, assessment, finding_ids=None):
    from .config import settings
    context, findings, coverage, current = prepare_context(db, user, assessment, finding_ids)
    blockers = []
    if not current:
        blockers.append("latest_revision")
    if not settings().model_api_key:
        blockers.append("model_key")
    if not context["findings"]:
        blockers.append("findings")
    if any(not ids for ids in coverage.values()):
        blockers.append("published_sources")
    return {
        "assessment_id": assessment.id, "ready": not blockers, "blockers": blockers,
        "model_configured": bool(settings().model_api_key), "current": current,
        "finding_count": len(findings), "selected_count": len(context["findings"]),
        "selected_ids": [f["id"] for f in context["findings"]],
        "findings": [{"id": f.id, "criterion_code": f.criterion_code, "title": f.title,
                      "critical": f.critical} for f in findings],
        "source_count": len(context["sources"]),
        "sources": [{k: s[k] for k in ("id", "code", "revision", "title", "criterion_codes")} for s in context["sources"]],
        "uncovered_ids": [fid for fid, ids in coverage.items() if not ids],
        "score": context["scoring"], "model": settings().model_id,
        "notice": "A disponibilidade de fontes não comprova a adequação das recomendações. Reveja o resultado."
    }
