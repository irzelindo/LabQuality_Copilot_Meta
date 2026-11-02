"""Load reviewed SLIPTA reference drafts into one institution, without publishing them.

Run from backend/ so the existing root .env selects the intended database.
"""
import argparse
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import session_factory
from .models import Document, User
from .operations import add_document
from .schemas import DocumentIn


SOURCE_DIR = Path(__file__).resolve().parents[1] / "samples" / "slipta_sources"


@dataclass(frozen=True)
class Source:
    code: str
    title: str
    criterion_codes: tuple[str, ...]


SOURCES = (
    Source("SLIPTA-REF-GESTAO-2023", "Referência de verificação SLIPTA V3 — gestão e revisão", ("1.5", "2.5", "2.9")),
    Source("SLIPTA-REF-PESSOAL-2023", "Referência de verificação SLIPTA V3 — pessoal e melhoria", ("3.6", "3.10", "11.1")),
    Source("SLIPTA-REF-SEGURANCA-2023", "Referência de verificação SLIPTA V3 — instalações e segurança",
           ("12.6", "12.11", "12.14", "12.23")),
)


def source_bodies() -> list[DocumentIn]:
    bodies = []
    for source in SOURCES:
        content = (SOURCE_DIR / f"{source.code}.txt").read_text(encoding="utf-8").strip()
        if len(content) > 6000 or any(f"{code} —" not in content for code in source.criterion_codes):
            raise ValueError(f"Fonte {source.code} incompatível com os critérios ou com o limite de contexto Meta.")
        bodies.append(DocumentIn(code=source.code, title=source.title, content=content,
                                 criterion_codes=list(source.criterion_codes)))
    return bodies


def plan(db: Session, actor: User) -> list[tuple[DocumentIn, str]]:
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
        else:
            raise ValueError(f"{body.code} já tem uma revisão diferente ou retirada nesta instituição. "
                             "Reveja-a e crie uma nova revisão pela interface; nenhuma fonte foi criada.")
    return result


def import_sources(db: Session, actor: User, *, apply: bool) -> list[tuple[str, str]]:
    """Preflight all three sources, then create drafts in the caller's transaction."""
    pending = plan(db, actor)
    if apply:
        for body, status in pending:
            if status == "new":
                add_document(body, db=db, user=actor)
    return [(body.code, status) for body, status in pending]


def main():
    parser = argparse.ArgumentParser(description="Pré-validar ou criar três fontes SLIPTA como rascunhos controlados.")
    parser.add_argument("--admin-email", default="admin@labquality.local")
    parser.add_argument("--apply", action="store_true", help="Criar rascunhos; exige revisão e aprovação na aplicação.")
    args = parser.parse_args()
    try:
        with session_factory()() as db:
            actor = db.scalar(select(User).where(User.email == args.admin_email.lower(),
                                                  User.active.is_(True), User.role == "admin"))
            if actor is None:
                raise ValueError("Administrador activo não encontrado. Indique --admin-email.")
            result = import_sources(db, actor, apply=args.apply)
            if args.apply:
                db.commit()
        for code, status in result:
            print(f"{code}: {'rascunho criado' if args.apply and status == 'new' else 'já existente' if status == 'unchanged' else 'por criar'}")
        print("Concluído. Revise, aprove com outra conta e publique em Documentos." if args.apply
              else "Só consulta: nenhum documento foi criado. Use --apply após conferir as fontes.")
    except (ValueError, OSError) as error:
        parser.exit(2, f"Importação interrompida: {error}\n")


if __name__ == "__main__":
    main()
