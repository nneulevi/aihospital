"""Shared Project2 database environment helpers for local E2E scripts."""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import quote


DEFAULT_PROJECT2_DSN = "postgresql://postgres:postgres@localhost:5432/hospital"


def _read_env_assignment(root: Path, filename: str, name: str) -> str | None:
    env_file = root / "scripts" / filename
    if not env_file.exists():
        return None

    try:
        content = env_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        content = env_file.read_text(encoding="utf-8-sig")

    match = re.search(rf"\$env:{re.escape(name)}\s*=\s*['\"]([^'\"]+)['\"]", content)
    return match.group(1).strip() if match else None


def get_project2_db_dsn(root: Path) -> str:
    explicit_dsn = os.getenv("PROJECT2_DB_DSN")
    if explicit_dsn:
        return explicit_dsn

    local_dsn = _read_env_assignment(root, "project2_env.local.ps1", "PROJECT2_DB_DSN")
    if local_dsn:
        return local_dsn

    username = (
        os.getenv("PROJECT2_DB_USERNAME")
        or _read_env_assignment(root, "project2_env.local.ps1", "PROJECT2_DB_USERNAME")
        or "postgres"
    )
    password = os.getenv("PROJECT2_DB_PASSWORD") or _read_env_assignment(
        root, "project2_env.local.ps1", "PROJECT2_DB_PASSWORD"
    )
    if password:
        return f"postgresql://{quote(username)}:{quote(password)}@localhost:5432/hospital"

    return DEFAULT_PROJECT2_DSN
