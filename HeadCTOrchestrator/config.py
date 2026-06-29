"""Configuration for the Head CT AI Orchestrator."""

from __future__ import annotations

import os
from pathlib import Path


SERVICE_DIR = Path(__file__).resolve().parent
OUTPUT_ROOT = Path(os.getenv("ORCH_OUTPUT_ROOT", SERVICE_DIR / "orchestrator_outputs"))

API_PREFIX = "/api/head-ct-ai"
MODULE_NAME = "head_ct_ai_orchestrator"
MODULE_VERSION = os.getenv("ORCH_MODULE_VERSION", "v1.0.0")

FILTER_BASE_URL = os.getenv("FILTER_BASE_URL", "http://localhost:8000")
FILTER_TIMEOUT_SECONDS = float(os.getenv("FILTER_TIMEOUT_SECONDS", "300"))
FILTER_POLL_INTERVAL_SECONDS = float(os.getenv("FILTER_POLL_INTERVAL_SECONDS", "1"))
FILTER_POLL_MAX_ATTEMPTS = int(os.getenv("FILTER_POLL_MAX_ATTEMPTS", "300"))

LESION_SERVICE_ENABLED = os.getenv("LESION_SERVICE_ENABLED", "false").lower() == "true"
LESION_BASE_URL = os.getenv("LESION_BASE_URL", "http://localhost:8020")
LESION_TIMEOUT_SECONDS = float(os.getenv("LESION_TIMEOUT_SECONDS", "300"))
LESION_POLL_INTERVAL_SECONDS = float(os.getenv("LESION_POLL_INTERVAL_SECONDS", "1"))
LESION_POLL_MAX_ATTEMPTS = int(os.getenv("LESION_POLL_MAX_ATTEMPTS", "300"))
LESION_REQUESTED_TYPES = os.getenv("LESION_REQUESTED_TYPES", "hemorrhage")
LESION_SKIP_ON_SEVERE_ARTIFACT = os.getenv("LESION_SKIP_ON_SEVERE_ARTIFACT", "false").lower() == "true"

RAG_ENABLED = os.getenv("RAG_ENABLED", "false").lower() == "true"
RAG_VECTOR_BACKEND = os.getenv("RAG_VECTOR_BACKEND", "pgvector").strip().lower()
RAG_DB_DSN = os.getenv("RAG_DB_DSN", "").strip()
RAG_STRICT_MODE = os.getenv("RAG_STRICT_MODE", "true").lower() == "true"
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
RAG_RECALL_TOP_N = int(os.getenv("RAG_RECALL_TOP_N", "20"))
RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.05"))
RAG_EMBEDDING_DIM = int(os.getenv("RAG_EMBEDDING_DIM", "1536"))
RAG_EMBEDDING_PROVIDER = os.getenv("RAG_EMBEDDING_PROVIDER", "deterministic").strip().lower()
RAG_HNSW_EF_SEARCH = int(os.getenv("RAG_HNSW_EF_SEARCH", "80"))
RAG_RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "false").lower() == "true"
RAG_RERANK_PROVIDER = os.getenv("RAG_RERANK_PROVIDER", "dashscope").strip().lower()
RAG_RERANK_TOP_N = int(os.getenv("RAG_RERANK_TOP_N", str(RAG_TOP_K)))
RAG_RERANK_TIMEOUT_SECONDS = float(os.getenv("RAG_RERANK_TIMEOUT_SECONDS", "30"))
RAG_CHUNK_MAX_CHARS = int(os.getenv("RAG_CHUNK_MAX_CHARS", "900"))
RAG_CHUNK_OVERLAP_CHARS = int(os.getenv("RAG_CHUNK_OVERLAP_CHARS", "160"))
DEPLOY_ENV = os.getenv("HEADCT_DEPLOY_ENV", os.getenv("APP_ENV", "local")).strip().lower()
REDIS_ENABLED = os.getenv("REDIS_ENABLED", "false").lower() == "true"
REDIS_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0").strip()
REDIS_CONNECT_TIMEOUT_SECONDS = float(os.getenv("REDIS_CONNECT_TIMEOUT_SECONDS", "2"))
REDIS_SOCKET_TIMEOUT_SECONDS = float(os.getenv("REDIS_SOCKET_TIMEOUT_SECONDS", "3"))
CACHE_RAG_RETRIEVAL_TTL_SECONDS = int(os.getenv("CACHE_RAG_RETRIEVAL_TTL_SECONDS", "1800"))
CACHE_LLM_RESPONSE_TTL_SECONDS = int(os.getenv("CACHE_LLM_RESPONSE_TTL_SECONDS", "1800"))
CACHE_MODEL_RESULT_TTL_SECONDS = int(os.getenv("CACHE_MODEL_RESULT_TTL_SECONDS", "86400"))
CACHE_PROJECT2_DICT_TTL_SECONDS = int(os.getenv("CACHE_PROJECT2_DICT_TTL_SECONDS", "3600"))
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", os.getenv("ALI_BAILIAN_API_KEY", "")).strip()
DASHSCOPE_EMBEDDING_BASE_URL = os.getenv(
    "DASHSCOPE_EMBEDDING_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
).rstrip("/")
DASHSCOPE_EMBEDDING_MODEL = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4").strip()
DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS = float(os.getenv("DASHSCOPE_EMBEDDING_TIMEOUT_SECONDS", "30"))
DASHSCOPE_RERANK_BASE_URL = os.getenv(
    "DASHSCOPE_RERANK_BASE_URL",
    "https://dashscope.aliyuncs.com",
).rstrip("/")
DASHSCOPE_RERANK_MODEL = os.getenv("DASHSCOPE_RERANK_MODEL", "gte-rerank-v2").strip()
LLM_ENABLED = os.getenv("LLM_ENABLED", "false").lower() == "true"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "rule_template").strip().lower()
LLM_STRICT_MODE = os.getenv("LLM_STRICT_MODE", "true").lower() == "true"
ALI_BAILIAN_API_KEY = os.getenv("ALI_BAILIAN_API_KEY", "").strip()
ALI_BAILIAN_BASE_URL = os.getenv("ALI_BAILIAN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1").rstrip("/")
ALI_BAILIAN_MODEL = os.getenv("ALI_BAILIAN_MODEL", "qwen-plus").strip()
ALI_BAILIAN_TIMEOUT_SECONDS = float(os.getenv("ALI_BAILIAN_TIMEOUT_SECONDS", "30"))

HOST = os.getenv("ORCH_HOST", "0.0.0.0")
PORT = int(os.getenv("ORCH_PORT", "8010"))
