from urllib.parse import quote, urljoin, urlparse
import httpx
from .config import settings
from .schemas import AssessmentIn, ODKIn


def nested(value, path: str):
    if path in value:
        return value[path]
    current = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def fetch_odk(body: ODKIn) -> list[AssessmentIn]:
    cfg = settings()
    base = cfg.odk_url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname:
        raise ValueError("LQ_ODK_URL deve usar HTTPS.")
    path = f"/v1/projects/{body.project_id}/forms/{quote(body.form_id, safe='')}.svc/Submissions"
    url = base + path + "?$top=100"
    records = []
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
                records.append(AssessmentIn(source=f"odk:{body.project_id}:{body.form_id}", external_id=str(stable_id),
                    source_revision=str(nested(row, body.revision_field) or ""), laboratory_code=str(lab_code),
                    instrument_code=body.instrument_code, instrument_version=body.instrument_version,
                    assessment_date=str(assessment_date)[:10],
                    answers={code: {"value": nested(row, field), "comment": ""} for code, field in body.criterion_fields.items()}))
                if len(records) > 500:
                    raise ValueError("Limite de 500 avaliações por sincronização. Divida a origem em lotes.")
            next_url = data.get("@odata.nextLink")
            if not next_url:
                return records
            url = urljoin(url, next_url)
            target = urlparse(url)
            if (target.scheme, target.netloc) != (parsed.scheme, parsed.netloc) or not target.path.startswith(parsed.path + path):
                raise ValueError("A paginação ODK apontou para um endereço inesperado.")
    raise ValueError("A sincronização excedeu o limite de páginas.")
