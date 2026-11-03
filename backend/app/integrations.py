from urllib.parse import quote, urljoin, urlparse
import httpx
from .config import settings
from .schemas import AssessmentIn, ODKIn
from .demo import PILOT


def nested(value, path: str):
    if path in value:
        return value[path]
    if path.replace(".", "/") in value:
        return value[path.replace(".", "/")]
    current = value
    for part in path.replace("/", ".").split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def fetch_odk_with_metadata(body: ODKIn) -> tuple[list[AssessmentIn], list[dict]]:
    cfg = settings()
    base = cfg.odk_url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("LQ_ODK_URL deve usar HTTPS.")
    pilot = body.instrument_code == PILOT["instrument_code"]
    if pilot:
        if body.form_id != PILOT["form_id"] or body.instrument_version != PILOT["instrument_version"]:
            raise ValueError("O formulário e a versão não correspondem ao piloto SLIPTA configurado.")
        scores = {c["code"]: c["odk"]["score"] for c in PILOT["criteria"]}
        na_fields = {c["code"]: c["odk"]["na"] for c in PILOT["criteria"]}
        comment_fields = {c["code"]: c["odk"]["comment"] for c in PILOT["criteria"]}
        # The checked XLSForm owns the mapping: callers cannot swap calculated fields.
        body = body.model_copy(update={"stable_id_field": PILOT["identity_field"],
            "laboratory_code_field": PILOT["laboratory_code_field"],
            "assessment_date_field": PILOT["assessment_date_field"],
            "revision_field": PILOT["revision_field"]})
    else:
        scores, na_fields, comment_fields = body.criterion_fields, body.na_fields, body.comment_fields
        if not scores:
            raise ValueError("Indique o mapeamento dos critérios do instrumento.")
    path = f"/v1/projects/{body.project_id}/forms/{quote(body.form_id, safe='')}.svc/Submissions"
    url = base + path + "?$top=100"
    records = []
    metadata = []
    with httpx.Client(auth=(cfg.odk_email, cfg.odk_password), timeout=45, follow_redirects=False) as client:
        for _ in range(100):
            page = client.get(url)
            page.raise_for_status()
            data = page.json()
            for row in data.get("value", []):
                stable_id = nested(row, body.stable_id_field)
                lab_code = nested(row, body.laboratory_code_field)
                assessment_date = nested(row, body.assessment_date_field)
                if stable_id is None or lab_code is None or assessment_date is None:
                    raise ValueError("Uma submissão não contém a identidade estável, laboratório ou data mapeados.")
                answers = {}
                for code, field in scores.items():
                    raw = nested(row, field)
                    selections = [nested(row, path) for path in na_fields.get(code, [])]
                    comments = [str(value).strip() for path in comment_fields.get(code, [])
                                if (value := nested(row, path)) not in (None, "")]
                    note = " | ".join(dict.fromkeys(comments))[:5000]
                    fully_na = bool(selections) and all(value == "na" for value in selections)
                    if pilot and any(value in (None, "") for value in selections):
                        raw = None  # Incomplete subitems cannot be treated as a zero-point finding.
                    if fully_na and not note:
                        raise ValueError(f"A submissão {stable_id} assinala {code} como NA sem justificação.")
                    answers[code] = {"value": None if fully_na or raw in (None, "") else raw,
                                     "comment": note, "not_applicable": fully_na}
                records.append(AssessmentIn(source=f"odk:{body.project_id}:{body.form_id}", external_id=str(stable_id),
                    source_revision=str(nested(row, body.revision_field) or ""), laboratory_code=str(lab_code),
                    instrument_code=body.instrument_code, instrument_version=body.instrument_version,
                    assessment_date=str(assessment_date)[:10],
                    answers=answers, reason="Importado da submissão ODK; rever achados antes de propor acções."))
                if pilot:
                    lab_name = nested(row, "tt_pp_01.tf_nome_laboratorio")
                    metadata.append({"laboratory_code": str(lab_code),
                        "laboratory_name": str(lab_name).strip()[:200] if lab_name is not None else ""})
                if len(records) > 500:
                    raise ValueError("Limite de 500 avaliações por sincronização. Divida a origem em lotes.")
            next_url = data.get("@odata.nextLink")
            if not next_url:
                return records, metadata
            url = urljoin(url, next_url)
            target = urlparse(url)
            if (target.scheme, target.netloc) != (parsed.scheme, parsed.netloc) or not target.path.startswith(parsed.path + path):
                raise ValueError("A paginação ODK apontou para um endereço inesperado.")
    raise ValueError("A sincronização excedeu o limite de páginas.")


def fetch_odk(body: ODKIn) -> list[AssessmentIn]:
    return fetch_odk_with_metadata(body)[0]
