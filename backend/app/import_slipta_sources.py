"""Load reviewed SLIPTA reference drafts into one institution, without publishing them.

Run from backend/ so the existing root .env selects the intended database.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import session_factory
from .demo import PILOT
from .models import Document, User
from .operations import add_document
from .schemas import DocumentIn


SOURCE_DIR = Path(__file__).resolve().parents[1] / "samples" / "slipta_sources"


@dataclass(frozen=True)
class Source:
    code: str
    title: str
    criterion_codes: tuple[str, ...]


SECTION_TITLES = (
    "Documentos e registos", "Organização e liderança", "Gestão de pessoal", "Foco no cliente",
    "Gestão de equipamentos", "Avaliação", "Fornecedores e inventário", "Gestão dos processos",
    "Gestão da informação", "Eventos não conformes", "Melhoria contínua", "Instalações e segurança",
)

SOURCES = tuple(
    Source(f"SLIPTA-SEC-{number:02d}-2023", f"SLIPTA V3 — Secção {number}: {title}",
           tuple(criterion["code"] for criterion in PILOT["criteria"]
                 if criterion["section"] == f"{number:02d} {title}"))
    for number, title in enumerate(SECTION_TITLES, 1)
)


def source_bodies() -> list[DocumentIn]:
    instrument_codes = [criterion["code"] for criterion in PILOT["criteria"]]
    mapped_codes = [code for source in SOURCES for code in source.criterion_codes]
    if len(SOURCES) != 12 or len(mapped_codes) != len(set(mapped_codes)) or set(mapped_codes) != set(instrument_codes):
        raise ValueError("As secções das fontes não correspondem aos critérios do instrumento piloto.")
    lines = (SOURCE_DIR / "criterion_evidence.tsv").read_text(encoding="utf-8").splitlines()
    if any(line.count("\t") != 1 for line in lines):
        raise ValueError("O catálogo de evidências por critério tem linhas inválidas.")
    evidence = dict(line.split("\t", 1) for line in lines)
    if len(evidence) != len(lines) or set(evidence) != set(instrument_codes) or any(len(value) < 35 for value in evidence.values()):
        raise ValueError("O catálogo de evidências deve cobrir uma vez cada critério do instrumento.")
    bodies = []
    for source in SOURCES:
        content = (SOURCE_DIR / f"{source.code}.txt").read_text(encoding="utf-8").strip()
        expected_entries = [f"{criterion['code']} — {criterion['title'].removeprefix(criterion['code']).strip()}"
                            f" | Evidência a verificar: {evidence[criterion['code']]}"
                            for criterion in PILOT["criteria"] if criterion["code"] in source.criterion_codes]
        if len(content) > 6000 or any(entry not in content for entry in expected_entries):
            raise ValueError(f"Fonte {source.code} incompatível com os critérios ou com o limite de contexto Meta.")
        bodies.append(DocumentIn(code=source.code, title=source.title, content=content,
                                 criterion_codes=list(source.criterion_codes)))
    return bodies


def plan(db: Session, actor: User, *, new_revisions: bool = False) -> list[tuple[DocumentIn, str]]:
    if not actor.active or actor.role != "admin":
        raise ValueError("É necessária uma conta de administrador activa da instituição.")
    result = []
    for body in source_bodies():
        existing = db.scalar(select(Document).where(
            Document.organization_id == actor.organization_id,
            Document.scope_key == "organization", Document.code == body.code
        ).order_by(Document.revision.desc()).limit(1))
        if existing is None:
            result.append((body, "new"))
        elif (existing.status != "withdrawn" and existing.title == body.title
              and existing.content == body.content and existing.criterion_codes == body.criterion_codes):
            result.append((body, "unchanged"))
        elif existing.status != "withdrawn" and new_revisions:
            result.append((body, "revised"))
        else:
            raise ValueError(f"{body.code} já tem uma revisão diferente ou retirada nesta instituição. "
                             "Confirme a revisão e use --new-revisions se não estiver retirado; nenhuma fonte foi criada.")
    return result


def import_sources(db: Session, actor: User, *, apply: bool, new_revisions: bool = False) -> list[tuple[str, str]]:
    """Preflight all twelve sources, then create drafts in the caller's transaction."""
    pending = plan(db, actor, new_revisions=new_revisions)
    if apply:
        for body, status in pending:
            if status in {"new", "revised"}:
                add_document(body, db=db, user=actor)
    return [(body.code, status) for body, status in pending]


def main():
    parser = argparse.ArgumentParser(description="Pré-validar ou criar doze fontes SLIPTA como rascunhos controlados.")
    parser.add_argument("--admin-email", default="admin@labquality.local")
    parser.add_argument("--apply", action="store_true", help="Criar rascunhos; exige revisão e aprovação na aplicação.")
    parser.add_argument("--new-revisions", action="store_true", help="Criar novas revisões para fontes existentes com texto alterado.")
    args = parser.parse_args()
    try:
        with session_factory()() as db:
            actor = db.scalar(select(User).where(User.email == args.admin_email.lower(),
                                                  User.active.is_(True), User.role == "admin"))
            if actor is None:
                raise ValueError("Administrador activo não encontrado. Indique --admin-email.")
            result = import_sources(db, actor, apply=args.apply, new_revisions=args.new_revisions)
            if args.apply:
                db.commit()
        for code, status in result:
            label = {"new": "rascunho criado" if args.apply else "por criar",
                     "revised": "nova revisão em rascunho" if args.apply else "nova revisão por criar",
                     "unchanged": "já existente"}[status]
            print(f"{code}: {label}")
        print("Concluído. Revise, aprove com outra conta e publique em Documentos." if args.apply
              else "Só consulta: nenhum documento foi criado. Use --apply após conferir as fontes.")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Importação interrompida: {error}\n")


if __name__ == "__main__":
    main()
