import argparse
import os
from dotenv import load_dotenv
from alembic import command
from alembic.config import Config
from sqlalchemy import select
from .database import session_factory
from .demo import seed_demo
from .models import Organization, User
from .security import passwords


def main():
    load_dotenv("../.env")
    load_dotenv(".env")
    parser = argparse.ArgumentParser(description="Apply migrations and optionally create explicit local demo data.")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--admin-email")
    parser.add_argument("--organization", default="Minha instituição")
    args = parser.parse_args()
    command.upgrade(Config("alembic.ini"), "head")
    with session_factory()() as db:
        if args.demo:
            result = seed_demo(db, os.environ.get("LQ_DEMO_PASSWORD", ""))
            db.commit()
            print("Demonstração já existente." if result.get("already_exists") else "Criados três laboratórios, nove avaliações e seis contas de demonstração.")
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
