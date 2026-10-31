"""Reference imports create drafts only. Existing independent approval stays mandatory."""
from fastapi import HTTPException
from pydantic import Field
from sqlalchemy import select
from .api import ACTOR, DB, router
from .models import Document, User
from .operations import add_document
from .schemas import DocumentIn, Schema
from .security import role, audit


class SourceDocument(Schema):
    code: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=3, max_length=250)
    content: str = Field(min_length=20, max_length=100000)
    criterion_codes: list[str] = Field(min_length=1, max_length=1000)


class ReferencePack(Schema):
    pack_version: str = Field(pattern=r"^slipta-sources-v1$")
    provenance: dict = Field(max_length=20)
    documents: list[SourceDocument] = Field(min_length=1, max_length=200)


@router.post("/reference-packs")
def import_pack(body: ReferencePack, dry_run: bool = False, db=DB, user: User = ACTOR):
    role(user, {"admin"})
    if len({d.code for d in body.documents}) != len(body.documents):
        raise HTTPException(422, "O pacote contém códigos documentais duplicados.")
    result = {"created": 0, "unchanged": 0, "document_ids": [], "dry_run": dry_run,
              "notice": "Os documentos novos ficam em rascunho e exigem revisão e aprovação por outra pessoa."}
    for item in body.documents:
        previous = db.scalar(select(Document).where(Document.organization_id == user.organization_id,
            Document.scope_key == "organization", Document.code == item.code)
            .order_by(Document.revision.desc()).limit(1))
        if previous and all(getattr(previous, k) == v for k, v in item.model_dump().items()):
            result["unchanged"] += 1
            result["document_ids"].append(previous.id)
            continue
        result["created"] += 1
        if not dry_run:
            added = add_document(DocumentIn(**item.model_dump()), db, user)
            row = db.get(Document, added["id"])
            audit(db, user, "reference_pack.imported", row, {
                "pack_version": body.pack_version,
                "pdf_sha256": str(body.provenance.get("pdf_sha256", ""))[:64],
                "xlsform_sha256": str(body.provenance.get("xlsform_sha256", ""))[:64]})
            result["document_ids"].append(added["id"])
    return result
