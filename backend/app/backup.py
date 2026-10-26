"""SQLite development backup. Recovery is into a new, empty destination only."""
import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy.engine import make_url
from .config import settings


def create_backup(destination: Path) -> Path:
    url = make_url(settings().database_url)
    if url.get_backend_name() != "sqlite" or not url.database or url.database == ":memory:":
        raise ValueError("Esta ferramenta destina-se ao SQLite local. Use pg_dump para PostgreSQL.")
    source = Path(url.database).resolve()
    if not source.is_file():
        raise ValueError("Base de dados não encontrada.")
    target = destination.resolve() / datetime.now(timezone.utc).strftime("labquality-%Y%m%dT%H%M%S%fZ")
    target.mkdir(parents=True, exist_ok=False)
    with sqlite3.connect(source) as original, sqlite3.connect(target / "database.sqlite") as backup:
        original.backup(backup)
    storage = Path(settings().storage_dir).resolve()
    if storage.exists():
        shutil.copytree(storage, target / "storage")
    else:
        (target / "storage").mkdir()
    files = {p.relative_to(target).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in target.rglob("*") if p.is_file()}
    (target / "manifest.json").write_text(json.dumps({"format": "labquality-sqlite-v1", "files": files}, indent=2), encoding="utf-8")
    return target


def restore_backup(source: Path, destination: Path) -> Path:
    source, destination = source.resolve(), destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise ValueError("O destino da recuperação deve estar vazio. Nenhum ficheiro foi substituído.")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "labquality-sqlite-v1":
        raise ValueError("Formato de backup desconhecido.")
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file() and p.name != "manifest.json"}
    if ("database.sqlite" not in manifest["files"] or actual != set(manifest["files"]) or
            not (source / "storage").is_dir() or any(p.is_symlink() for p in source.rglob("*"))):
        raise ValueError("A integridade do conjunto de ficheiros não foi confirmada.")
    for relative, digest in manifest["files"].items():
        path = (source / relative).resolve()
        if not path.is_relative_to(source) or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError("A integridade do backup não foi confirmada.")
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source / "database.sqlite", destination / "database.sqlite")
    shutil.copytree(source / "storage", destination / "storage")
    return destination


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="operation", required=True)
    create = sub.add_parser("create")
    create.add_argument("destination", type=Path)
    restore = sub.add_parser("restore")
    restore.add_argument("source", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.operation == "create":
        print(create_backup(args.destination))
    else:
        print(restore_backup(args.source, args.destination))
        print("Configure LQ_DATABASE_URL e LQ_STORAGE_DIR para o destino recuperado antes de iniciar a API.")


if __name__ == "__main__":
    main()
