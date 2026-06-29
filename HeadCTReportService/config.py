"""Configuration for the Head CT report service."""

from __future__ import annotations

import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent
API_PREFIX = "/api/v1"
MODULE_NAME = "head_ct_report_service"
MODULE_VERSION = os.getenv("REPORT_MODULE_VERSION", "v1.0.0")

REPORT_DB_DSN = os.getenv("REPORT_DB_DSN", os.getenv("RAG_DB_DSN", "")).strip()
REPORT_AUTO_INIT_DB = os.getenv("REPORT_AUTO_INIT_DB", "true").lower() == "true"

ORCHESTRATOR_BASE_URL = os.getenv("ORCHESTRATOR_BASE_URL", "http://localhost:8010").rstrip("/")
ORCHESTRATOR_TIMEOUT_SECONDS = float(os.getenv("ORCHESTRATOR_TIMEOUT_SECONDS", "30"))

EMR_BASE_URL = os.getenv("EMR_BASE_URL", "").rstrip("/")
EMR_TIMEOUT_SECONDS = float(os.getenv("EMR_TIMEOUT_SECONDS", "15"))
EMR_ENABLED = os.getenv("EMR_ENABLED", "false").lower() == "true"
EMR_SERVICE_TOKEN = os.getenv("EMR_SERVICE_TOKEN", "").strip()

TRUST_IDENTITY_HEADERS = os.getenv("REPORT_TRUST_IDENTITY_HEADERS", "true").lower() == "true"
DEPLOYMENT_MODE = os.getenv("REPORT_DEPLOYMENT_MODE", "development").strip().lower()

HOST = os.getenv("REPORT_HOST", "0.0.0.0")
PORT = int(os.getenv("REPORT_PORT", "8030"))
