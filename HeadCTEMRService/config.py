"""Configuration for the EMR integration service."""

from __future__ import annotations

import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent
MODULE_NAME = "head_ct_emr_service"
MODULE_VERSION = os.getenv("EMR_MODULE_VERSION", "v1.0.0")
API_PREFIX = "/api/v1"

EMR_DB_DSN = os.getenv("EMR_DB_DSN", os.getenv("REPORT_DB_DSN", os.getenv("RAG_DB_DSN", ""))).strip()
EMR_AUTO_INIT_DB = os.getenv("EMR_AUTO_INIT_DB", "true").lower() == "true"
EMR_SERVICE_TOKEN = os.getenv("EMR_SERVICE_TOKEN", "").strip()

HOST = os.getenv("EMR_HOST", "127.0.0.1")
PORT = int(os.getenv("EMR_PORT", "8040"))

