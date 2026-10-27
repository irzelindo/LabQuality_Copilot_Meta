"""One-time, locally executed SLIPTA ODK import with count and lab safeguards.

Run from backend/ so Settings reads the root .env and the local database URL.
No credentials or raw answers are printed or persisted outside the assessment store.
"""
import argparse
import re
from pathlib import Path

import httpx
from fastapi import HTTPException
from sqlalchemy import select

from .backup import create_backup
from .config import settings
from .database import session_factory
from .demo import PILOT
from .integrations import fetch_odk_with_metadata
from .models import Instrument, Laboratory, User
from .schemas import ODKIn
from .services import import_assessments


def request(project_id: int) -> ODKIn:
    return ODKIn(project_id=project_id, form_id=PILOT["form_id"],
        stable_id_field=PILOT["identity_field"], laboratory_code_field=PILOT["laboratory_code_field"],
        assessment_date_field=PILOT["assessment_date_field"], instrument_code=PILOT["instrument_code"],
        instrument_version=PILOT["instrument_version"])


def laboratory_names(records, metadata) -> dict[str, str]:
    names: dict[str, set[str]] = {}
    for record, detail in zip(records, metadata, strict=True):
        names.setdefault(record.laboratory_code, set()).add(detail["laboratory_name"].strip())
    if any(len(variants) != 1 or not next(iter(variants)) or not re.fullmatch(r"[A-Za-z0-9_-]{1,60}", code)
           or len(next(iter(variants))) > 200 for code, variants in names.items()):
        raise ValueError("Código ou nome de laboratório ODK ausente, inconsistente ou inválido. Reveja as submissões.")
    return {code: next(iter(variants)) for code, variants in sorted(names.items())}


def check_scope(db, actor, names: dict[str, str]):
    instrument = db.scalar(select(Instrument).where(Instrument.organization_id == actor.organization_id,
        Instrument.code == PILOT["instrument_code"], Instrument.version == PILOT["instrument_version"],
        Instrument.published.is_(True)))
    expected = [{key: criterion[key] for key in ("code", "section", "title", "maximum", "critical")}
                for criterion in PILOT["criteria"]]
    if not instrument or instrument.scoring_rule != "sum_applicable_v1" or instrument.criteria != expected:
        raise ValueError("O instrumento piloto publicado não corresponde aos critérios e à pontuação esperados.")
    known = {lab.code: lab for lab in db.scalars(select(Laboratory).where(
        Laboratory.organization_id == actor.organization_id))}
    mismatches = [code for code, name in names.items() if code in known and known[code].name != name]
    if mismatches:
        raise ValueError("Os nomes dos laboratórios existentes não correspondem ao ODK para os códigos: "
                         + ", ".join(mismatches) + ". Confirme a correspondência antes de importar.")
    return {code: name for code, name in names.items() if code not in known}


def run(project_id: int, expected: int, admin_email: str, apply: bool, register_missing: bool):
    if project_id < 1 or expected < 1:
        raise ValueError("O projecto e a contagem esperada devem ser positivos.")
    cfg = settings()
    if not (cfg.odk_url and cfg.odk_email and cfg.odk_password):
        raise ValueError("Defina LQ_ODK_URL, LQ_ODK_EMAIL e LQ_ODK_PASSWORD no .env da raiz.")
    records, metadata = fetch_odk_with_metadata(request(project_id))
    if len(records) != expected:
        raise ValueError(f"Esperadas {expected} submissões; ODK devolveu {len(records)}. Nada foi gravado.")
    if len({(record.source, record.external_id) for record in records}) != expected:
        raise ValueError("O ODK devolveu identidades repetidas. Nada foi gravado.")
    names = laboratory_names(records, metadata)
    print(f"Formulário: {PILOT['form_id']} | projecto: {project_id} | submissões: {len(records)}")
    with session_factory()() as db:
        actor = db.scalar(select(User).where(User.email == admin_email.lower(), User.active.is_(True), User.role == "admin"))
        if not actor:
            raise ValueError("Administrador activo não encontrado. Indique --admin-email.")
        missing = check_scope(db, actor, names)
        for code, name in names.items():
            print(f"Laboratório {code}: {name} ({'por cadastrar' if code in missing else 'cadastrado'})")
        if missing and not register_missing:
            print("Para importar, cadastre os laboratórios em falta ou use --register-missing após conferir os nomes.")
            if apply:
                raise ValueError("Laboratórios em falta. Nada foi gravado.")
        else:
            transaction = db.begin_nested()
            try:
                for code, name in missing.items():
                    db.add(Laboratory(organization_id=actor.organization_id, code=code, name=name, region=""))
                db.flush()
                result = import_assessments(db, actor, records)
                print(f"Pré-validação: {result['created']} novas, {result['revised']} revisões, {result['unchanged']} inalteradas.")
            finally:
                transaction.rollback()
        if not apply:
            print("Só consulta: nenhuma avaliação ou laboratório foi gravado.")
            return
    backup = create_backup(Path("../backups"))
    print(f"Cópia de segurança criada: {backup}")
    with session_factory()() as db:
        actor = db.scalar(select(User).where(User.email == admin_email.lower(), User.active.is_(True), User.role == "admin"))
        if not actor:
            raise ValueError("Administrador activo não encontrado após o backup.")
        missing = check_scope(db, actor, names)
        if missing and not register_missing:
            raise ValueError("Há laboratórios por cadastrar. Nada foi gravado.")
        for code, name in missing.items():
            db.add(Laboratory(organization_id=actor.organization_id, code=code, name=name, region=""))
        db.flush()
        result = import_assessments(db, actor, records)
        db.commit()
    print(f"Importação concluída: {result['created']} novas, {result['revised']} revisões, {result['unchanged']} inalteradas.")


def main():
    parser = argparse.ArgumentParser(description="Pré-validar e importar submissões ODK do piloto SLIPTA.")
    parser.add_argument("--project-id", type=int, default=1)
    parser.add_argument("--expected", type=int, default=9)
    parser.add_argument("--admin-email", default="admin@labquality.local")
    parser.add_argument("--apply", action="store_true", help="Criar backup e aplicar o lote validado.")
    parser.add_argument("--register-missing", action="store_true", help="Cadastrar os códigos/nome ODK ainda ausentes.")
    args = parser.parse_args()
    try:
        run(args.project_id, args.expected, args.admin_email, args.apply, args.register_missing)
    except httpx.HTTPStatusError as error:
        parser.exit(2, f"Importação interrompida: ODK devolveu HTTP {error.response.status_code}. Nada foi gravado.\n")
    except httpx.RequestError:
        parser.exit(2, "Importação interrompida: não foi possível contactar o servidor ODK. Nada foi gravado.\n")
    except (ValueError, HTTPException) as error:
        parser.exit(2, f"Importação interrompida: {error}\n")


if __name__ == "__main__":
    main()
