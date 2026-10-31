from html import escape
from fastapi import HTTPException
from fastapi.responses import HTMLResponse
from .api import ACTOR, DB, router
from .ai import run_out
from .models import AIExecution, Action, Assessment, Laboratory, User
from .security import get_scoped, require_details


def e(value):
    return escape(str(value if value is not None else ""))


@router.get("/ai/runs/{run_id}/report.html", response_class=HTMLResponse)
def report(run_id: str, db=DB, user: User = ACTOR):
    require_details(user)
    run = get_scoped(db, AIExecution, run_id, user)
    data = run_out(db, run, user)
    if data["status"] != "completed":
        raise HTTPException(409, "O relatório exige uma análise concluída e fontes ainda publicadas.")
    assessment = get_scoped(db, Assessment, run.assessment_id, user)
    lab = get_scoped(db, Laboratory, run.laboratory_id, user)
    sources = {s["id"]: s for s in data["sources"]}
    body = []
    for index, rec in enumerate(run.result.get("recommendations", [])):
        citations = "".join("<blockquote>" + e(c["quote"]) + "<footer>" +
                    e(sources[c["source_id"]]["code"]) + " / v" +
                    e(sources[c["source_id"]]["revision"]) + "</footer></blockquote>" for c in rec["citations"])
        action = db.get(Action, run.accepted.get(str(index), "")) if str(index) in run.accepted else None
        action_text = f"Action status: {e(action.status)}. Due: {e(action.due_date)}." if action else "Awaiting human review."
        body.append(f"<article><h2>{index + 1}. {e(rec['title'])}</h2><p>{e(rec['justification'])}</p>"
                    f"<p>Priority proposed by model: {e(rec['priority'])}</p><ol>" +
                    "".join("<li>" + e(step) + "</li>" for step in rec["steps"]) +
                    f"</ol><p><b>Completion criterion:</b> {e(rec['completion_criterion'])}</p>{citations}<p>{action_text}</p></article>")
    document = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>LabQuality Copilot report</title>
    <style>body{{font:16px/1.6 system-ui,sans-serif;max-width:900px;margin:40px auto;padding:20px;color:#16363c}}
    h1{{color:#08776d}}article{{border-top:1px solid #ccdcd9;padding:20px 0;break-inside:avoid}}
    blockquote{{border-left:3px solid #08776d;padding:12px 18px;margin:15px 0;background:#f4f8f7}}
    footer,.meta{{color:#51666b;font-size:13px}}@media print{{body{{margin:0;max-width:none}}}}</style>
    <h1>LabQuality Copilot</h1><p>Improvement proposals for human review</p>
    <p class="meta">Laboratory: {e(lab.name)}<br>Assessment: {e(assessment.assessment_date)} / revision {assessment.revision}
    <br>Model: {e(run.model)} / prompt: {e(run.prompt_version)}<br>Run: {e(run.id)} / {e(run.created_at)}
    <br>Duration: {run.latency_ms / 1000:.1f}s / input tokens: {e(run.usage.get('input_tokens'))} / output tokens: {e(run.usage.get('output_tokens'))}</p>
    <p>{e(run.result.get('summary'))}</p>
    {"<p>Additional evidence is required. Review limitations before acting.</p>" if run.result.get("insufficient_evidence") else ""}
    {''.join(body)}
    <p class="meta">Quote matching checks source text and criterion links. A qualified person must review the meaning and suitability of each proposal.
    This report does not award SLIPTA recognition or accreditation. Use your browser Print command to save as PDF.</p></html>"""
    return HTMLResponse(document, headers={"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
                                          "Cache-Control": "no-store"})
