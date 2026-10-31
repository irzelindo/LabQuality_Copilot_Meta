"""Preview or import SLIPTA OData without modifying ODK or existing assessment history."""
import argparse
import json
from pathlib import Path
from urllib.parse import quote, urljoin, urlparse
import httpx
from sqlalchemy import select
from .config import settings
from .database import session_factory
from .models import Instrument, Laboratory, User
from .schemas import AssessmentIn
from .services import import_assessments
from .slipta_sources import catalog


def leaf(row, field):
    """Resolve an exact field name through nested OData groups. Ambiguity is an error."""
    matches = []
    def visit(value):
        if isinstance(value, dict):
            for key, item in value.items():
                if key == field or key.rsplit("/", 1)[-1] == field:
                    matches.append(item)
                elif isinstance(item, dict):
                    visit(item)
    visit(row)
    if len(matches) > 1:
        raise ValueError(f"Campo ambíguo na submissão: {field}")
    return matches[0] if matches else None


def to_assessment(row, instrument, project_id):
    stable_id = row.get("__id") or leaf(row, "instanceID")
    lab = leaf(row, "tf_numero_laboratorio")
    day = leaf(row, "df_data_auditoria_actual")
    if not stable_id or lab is None or not day:
        raise ValueError("Falta instanceID/__id, número de laboratório ou data da auditoria.")
    answers = {}
    for item in instrument["items"]:
        raw = [leaf(row, f) for f in item["answer_fields"]]
        comments = [str(leaf(row, f + "_comentarios") or "") for f in item["answer_fields"]]
        comments.append(str(leaf(row, item["field"] + "_comentarios") or ""))
        value = leaf(row, item["score_field"])
        explanation = ""
        if any(not isinstance(v, str) or v not in {"sim", "parcial", "nao", "na"} for v in raw):
            value = None
            explanation = "Respostas de origem em falta ou desconhecidas. Conferir no ODK."
        elif all(v == "na" for v in raw):
            value = None
            explanation = "Não aplicável na origem. Percentagem final suspensa para revisão do denominador."
        elif value is None:
            # Never evaluate arbitrary XLSForm expressions or guess a grouped score.
            explanation = "Campo calculado ausente. Confirmar pontuação na origem."
        elif isinstance(value, bool) or not str(value).replace(".0", "").isdigit():
            raise ValueError(f"Pontuação inválida para {item['code']}.")
        else:
            numeric = float(value)
            if not numeric.is_integer() or not 0 <= numeric <= item["maximum"]:
                raise ValueError(f"Pontuação fora do intervalo para {item['code']}.")
            value = int(numeric)
        comment = "\n".join(dict.fromkeys(c for c in [*comments, explanation] if c))
        if len(comment) > 5000:
            raise ValueError(f"Comentários excedem 5000 caracteres em {item['code']}.")
        answers[item["code"]] = {"value": value, "comment": comment}
    return AssessmentIn(
        source=f"odk:{project_id}:{instrument['form_id']}", external_id=str(stable_id),
        source_revision=str(row.get("__system", {}).get("updatedAt") or row.get("__system", {}).get("submissionDate") or ""),
        laboratory_code=str(lab).strip(), instrument_code="SLIPTA-V3-PILOT",
        instrument_version=instrument["version"], assessment_date=str(day)[:10], answers=answers,
        reason="Importação do XLSForm SLIPTA piloto. Pontuações calculadas recebidas da origem; sem classificação oficial.")


def fetch_rows(project, form_id):
    cfg = settings()
    base = cfg.odk_url.rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme != "https" or not parsed.hostname or not cfg.odk_email or not cfg.odk_password:
        raise ValueError("Configure LQ_ODK_URL (HTTPS), LQ_ODK_EMAIL e LQ_ODK_PASSWORD.")
    path = parsed.path + f"/v1/projects/{project}/forms/{quote(form_id, safe='')}.svc/Submissions"
    url = base + f"/v1/projects/{project}/forms/{quote(form_id, safe='')}.svc/Submissions?$top=100"
    rows = []
    with httpx.Client(auth=(cfg.odk_email, cfg.odk_password), timeout=45, follow_redirects=False) as client:
        for _ in range(100):
            response = client.get(url)
            response.raise_for_status()
            data = response.json()
            rows.extend(data.get("value", []))
            if len(rows) > 500:
                raise ValueError("Máximo de 500 avaliações. Divida a importação em lotes.")
            if not data.get("@odata.nextLink"):
                return rows
            url = urljoin(url, data["@odata.nextLink"])
            target = urlparse(url)
            if (target.scheme, target.netloc, target.path) != (parsed.scheme, parsed.netloc, path):
                raise ValueError("Destino de paginação ODK não autorizado.")
    raise ValueError("Limite de páginas ODK excedido.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-id", type=int, default=1)
    parser.add_argument("--expected", type=int, required=True)
    parser.add_argument("--xlsform", type=Path, required=True)
    parser.add_argument("--input", type=Path, help="Exportação JSON OData local, em vez de acesso remoto.")
    parser.add_argument("--admin-email")
    parser.add_argument("--register-missing", action="store_true")
    parser.add_argument("--apply", action="store_true", help="Gravar. Sem esta opção, faz apenas pré-validação.")
    args = parser.parse_args()
    instrument = catalog(args.xlsform)
    raw = json.loads(args.input.read_text(encoding="utf-8")) if args.input else fetch_rows(args.project_id, instrument["form_id"])
    rows = raw.get("value", []) if isinstance(raw, dict) else raw
    if not 1 <= args.expected <= 500 or len(rows) != args.expected:
        parser.error("A contagem recebida não coincide com --expected (1 a 500). Nenhum dado foi gravado.")
    records = [to_assessment(row, instrument, args.project_id) for row in rows]
    with session_factory()() as db:
        query = select(User).where(User.active.is_(True), User.role == "admin")
        if args.admin_email:
            query = query.where(User.email == args.admin_email.lower())
        admins = list(db.scalars(query))
        if len(admins) != 1:
            parser.error("Indique --admin-email de um administrador activo.")
        user = admins[0]
        existing = db.scalar(select(Instrument).where(Instrument.organization_id == user.organization_id,
            Instrument.code == "SLIPTA-V3-PILOT", Instrument.version == instrument["version"]))
        criteria = [{k: item[k] for k in ("code", "section", "title", "maximum")} | {"critical": False}
                    for item in instrument["items"]]
        if not existing:
            if not args.register_missing:
                parser.error("Falta instrumento. Use --register-missing após conferir o XLSForm.")
            db.add(Instrument(organization_id=user.organization_id, code="SLIPTA-V3-PILOT",
                version=instrument["version"], name="SLIPTA V3 / piloto técnico",
                description="Pesos do XLSForm fornecido. Sem atribuição oficial de estrelas. N/A exige revisão.",
                criteria=criteria))
        elif existing.criteria != criteria:
            parser.error("O instrumento existente tem critérios diferentes. Preserve a versão e registe uma nova.")
        for code in sorted({r.laboratory_code for r in records}):
            if not db.scalar(select(Laboratory).where(Laboratory.organization_id == user.organization_id, Laboratory.code == code)):
                if not args.register_missing:
                    parser.error("Falta laboratório. Registe-o ou use --register-missing após conferência.")
                db.add(Laboratory(organization_id=user.organization_id, code=code, name="Laboratório " + code))
        db.flush()
        result = import_assessments(db, user, records)
        result.pop("assessment_ids", None)
        result.pop("import_run_id", None)
        if args.apply:
            db.commit()
        else:
            db.rollback()
        print(json.dumps({"applied": args.apply, **result, "count": len(records),
                          "notice": "Conferir identidades antes de gravar se já existem avaliações importadas por outra ferramenta."}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except httpx.HTTPStatusError as error:
        raise SystemExit(f"ODK respondeu HTTP {error.response.status_code}. Nenhuma alteração aplicada.")
    except (ValueError, OSError) as error:
        raise SystemExit(str(error))
