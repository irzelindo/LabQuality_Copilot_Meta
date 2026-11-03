import argparse
import os
import re
from pathlib import Path
from dotenv import load_dotenv
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from .database import session_factory
from .demo import seed_demo, refresh_demo
from .backup import create_backup
from .models import Organization, User
from .security import passwords


def main():
    load_dotenv("../.env")
    load_dotenv(".env")
    parser = argparse.ArgumentParser(description="Apply migrations and optionally create explicit local demo data.")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--refresh-demo", action="store_true", help="Back up SQLite and replace only the isolated demo organization")
    parser.add_argument("--backup-dir", type=Path, default=Path(".backups"))
    parser.add_argument("--admin-email")
    parser.add_argument("--organization", default="Minha instituição")
    args = parser.parse_args()
    if args.demo and args.refresh_demo:
        parser.error("Escolha --demo ou --refresh-demo.")
    if args.refresh_demo:
        from .config import settings
        from sqlalchemy.engine import make_url
        url = make_url(settings().database_url)
        if url.get_backend_name() != "sqlite" or not url.database or not Path(url.database).is_file():
            raise SystemExit("A limpeza automática exige SQLite local existente. Para PostgreSQL, faça backup e migração controlada.")
        backup = create_backup(args.backup_dir)
        print(f"Backup anterior à limpeza: {backup}")
    command.upgrade(Config("alembic.ini"), "head")
    with session_factory()() as db:
        if args.demo:
            result = seed_demo(db, os.environ.get("LQ_DEMO_PASSWORD", ""))
            db.commit()
            print("Demonstração já existente." if result.get("already_exists") else "Criados três laboratórios, nove avaliações e seis contas de demonstração.")
        if args.refresh_demo:
            try:
                result = refresh_demo(db, os.environ.get("LQ_DEMO_PASSWORD", ""))
                db.commit()
            except Exception:
                db.rollback()
                raise
            from .config import settings
            storage = Path(settings().storage_dir).resolve()
            for key in result["deleted_evidence_keys"]:
                if re.fullmatch(r"[0-9a-f]{48}", key):
                    (storage / key).unlink(missing_ok=True)
            print("Demonstração limpa: nove avaliações SLIPTA simuladas, três momentos por laboratório.")
        if args.admin_email:
            password = os.environ.get("LQ_ADMIN_PASSWORD", "")
            if len(password) < 12 or "@" not in args.admin_email:
                raise SystemExit("Defina LQ_ADMIN_PASSWORD (mínimo 12 caracteres) e um email válido.")
            email = args.admin_email.lower()
            if db.scalar(select(User).where(User.email == email)):
                raise SystemExit("O email já existe. Nenhuma palavra-passe foi alterada.")
            org = Organization(name=args.organization)
            db.add(org)
            db.flush()
            db.add(User(organization_id=org.id, name="Administrador", email=email, role="admin",
                        password_hash=passwords.hash(password), laboratory_ids=[]))
            db.commit()
            print("Organização e administrador criados.")


if __name__ == "__main__":
    main()
