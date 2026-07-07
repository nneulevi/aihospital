"""Conversation memory storage and prompt-context assembly."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol

try:
    from HeadCTOrchestrator.rag import db
    from HeadCTOrchestrator.rag.embedding_provider import embed_text, pgvector_literal
except ImportError:  # pragma: no cover - direct script fallback.
    from rag import db  # type: ignore
    from rag.embedding_provider import embed_text, pgvector_literal  # type: ignore


RECENT_MESSAGE_LIMIT = 8
SEMANTIC_MEMORY_LIMIT = 6
SEMANTIC_MIN_SCORE = 0.12
SUMMARY_MAX_CHARS = 900
SUMMARY_COMPRESSION_MESSAGE_INTERVAL = 6
FACT_KEYWORDS = ("头痛", "恶心", "呕吐", "外伤", "高血压", "糖尿病", "病史", "用药", "过敏", "出血", "CT", "影像")
SEMANTIC_SYNONYMS = {
    "anticoagulant": {"warfarin", "anticoagulation", "blood", "thinner"},
    "anticoagulation": {"warfarin", "anticoagulant"},
    "warfarin": {"anticoagulant", "anticoagulation"},
    "allergy": {"allergic", "contrast"},
    "contrast": {"allergy", "allergic"},
    "hypertension": {"blood", "pressure"},
    "headache": {"pain"},
    "hemorrhage": {"bleeding", "blood"},
}


class ConversationStore(Protocol):
    def get_session(self, conversation_id: str) -> dict[str, Any] | None:
        ...

    def upsert_session(self, metadata: dict[str, Any]) -> dict[str, Any]:
        ...

    def append_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        ...

    def recent_messages(self, conversation_id: str, limit: int = RECENT_MESSAGE_LIMIT) -> list[dict[str, Any]]:
        ...

    def message_count(self, conversation_id: str) -> int:
        ...

    def append_semantic_memory(
        self,
        metadata: dict[str, Any],
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        ...

    def semantic_memories(self, payload: dict[str, Any], query_text: str, limit: int = SEMANTIC_MEMORY_LIMIT) -> list[dict[str, Any]]:
        ...

    def update_memory(
        self,
        conversation_id: str,
        summary: str,
        key_facts: list[str],
        unresolved_questions: list[str],
        summarized_message_count: int | None = None,
    ) -> None:
        ...


@dataclass
class _Session:
    metadata: dict[str, Any]
    summary: str = ""
    key_facts: list[str] = field(default_factory=list)
    unresolved_questions: list[str] = field(default_factory=list)
    summarized_message_count: int = 0


class InMemoryConversationStore:
    """Small test and development store implementing the production store interface."""

    def __init__(self) -> None:
        self._sessions: dict[str, _Session] = {}
        self._messages: dict[str, list[dict[str, Any]]] = {}
        self._semantic_memories: list[dict[str, Any]] = []

    def get_session(self, conversation_id: str) -> dict[str, Any] | None:
        session = self._sessions.get(conversation_id)
        if not session:
            return None
        return {
            **session.metadata,
            "summary": session.summary,
            "key_facts": list(session.key_facts),
            "unresolved_questions": list(session.unresolved_questions),
            "summarized_message_count": session.summarized_message_count,
        }

    def upsert_session(self, metadata: dict[str, Any]) -> dict[str, Any]:
        conversation_id = str(metadata["conversation_id"])
        existing = self._sessions.get(conversation_id)
        if existing:
            existing.metadata.update({key: value for key, value in metadata.items() if value is not None})
            return self.get_session(conversation_id) or dict(metadata)
        self._sessions[conversation_id] = _Session(metadata={key: value for key, value in metadata.items() if value is not None})
        self._messages.setdefault(conversation_id, [])
        return self.get_session(conversation_id) or dict(metadata)

    def append_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        self._messages.setdefault(conversation_id, []).append(
            {
                "sender": sender,
                "content": content,
                "structured_payload": structured_payload or {},
                "importance_score": importance_score,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def recent_messages(self, conversation_id: str, limit: int = RECENT_MESSAGE_LIMIT) -> list[dict[str, Any]]:
        messages = self._messages.get(conversation_id, [])
        return [dict(item) for item in messages[-limit:]]

    def message_count(self, conversation_id: str) -> int:
        return len(self._messages.get(conversation_id, []))

    def append_semantic_memory(
        self,
        metadata: dict[str, Any],
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        cleaned = clip_text(content, 1600)
        if not cleaned:
            return
        self._semantic_memories.append(
            {
                "conversation_id": metadata.get("conversation_id"),
                "role_scope": metadata.get("role_scope"),
                "patient_id": metadata.get("patient_id"),
                "visit_id": metadata.get("visit_id"),
                "medical_record_id": metadata.get("medical_record_id"),
                "scene": metadata.get("scene"),
                "sender": sender,
                "content": cleaned,
                "structured_payload": structured_payload or {},
                "importance_score": importance_score,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    def semantic_memories(self, payload: dict[str, Any], query_text: str, limit: int = SEMANTIC_MEMORY_LIMIT) -> list[dict[str, Any]]:
        metadata = session_metadata(payload, normalize_conversation_id(payload))
        query_tokens = semantic_tokens(query_text)
        ranked: list[dict[str, Any]] = []
        for item in self._semantic_memories:
            if not is_same_memory_scope(metadata, item):
                continue
            score = lexical_semantic_score(query_tokens, item["content"]) * float(item.get("importance_score") or 0.5)
            if score < SEMANTIC_MIN_SCORE:
                continue
            ranked.append({**item, "score": score, "provider": "in_memory_lexical"})
        ranked.sort(key=lambda item: item["score"], reverse=True)
        return ranked[:limit]

    def update_memory(
        self,
        conversation_id: str,
        summary: str,
        key_facts: list[str],
        unresolved_questions: list[str],
        summarized_message_count: int | None = None,
    ) -> None:
        session = self._sessions[conversation_id]
        session.summary = summary
        session.key_facts = dedupe_texts(key_facts)
        session.unresolved_questions = dedupe_texts(unresolved_questions)
        if summarized_message_count is not None:
            session.summarized_message_count = max(session.summarized_message_count, summarized_message_count)


class PostgresConversationStore:
    """Persistent conversation memory store backed by the RAG PostgreSQL database."""

    def get_session(self, conversation_id: str) -> dict[str, Any] | None:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT conversation_id, role_scope, user_id, patient_id, visit_id, medical_record_id,
                           scene, summary, key_facts, unresolved_questions, summarized_message_count
                    FROM conversation_sessions
                    WHERE conversation_id = %s
                    """,
                    (conversation_id,),
                )
                row = cur.fetchone()
        if not row:
            return None
        return {
            "conversation_id": row[0],
            "role_scope": row[1],
            "user_id": row[2],
            "patient_id": row[3],
            "visit_id": row[4],
            "medical_record_id": row[5],
            "scene": row[6],
            "summary": row[7] or "",
            "key_facts": list(row[8] or []),
            "unresolved_questions": list(row[9] or []),
            "summarized_message_count": int(row[10] or 0),
        }

    def upsert_session(self, metadata: dict[str, Any]) -> dict[str, Any]:
        conversation_id = str(metadata["conversation_id"])
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversation_sessions(
                        conversation_id, role_scope, user_id, patient_id, visit_id, medical_record_id, scene
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (conversation_id) DO UPDATE SET
                        role_scope = COALESCE(EXCLUDED.role_scope, conversation_sessions.role_scope),
                        user_id = COALESCE(EXCLUDED.user_id, conversation_sessions.user_id),
                        patient_id = COALESCE(EXCLUDED.patient_id, conversation_sessions.patient_id),
                        visit_id = COALESCE(EXCLUDED.visit_id, conversation_sessions.visit_id),
                        medical_record_id = COALESCE(EXCLUDED.medical_record_id, conversation_sessions.medical_record_id),
                        scene = COALESCE(EXCLUDED.scene, conversation_sessions.scene),
                        updated_at = NOW()
                    """,
                    (
                        conversation_id,
                        metadata.get("role_scope"),
                        metadata.get("user_id"),
                        metadata.get("patient_id"),
                        metadata.get("visit_id"),
                        metadata.get("medical_record_id"),
                        metadata.get("scene"),
                    ),
                )
            conn.commit()
        return self.get_session(conversation_id) or dict(metadata)

    def append_message(
        self,
        conversation_id: str,
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversation_messages(
                        conversation_id, sender, content, structured_payload, importance_score
                    )
                    VALUES (%s, %s, %s, %s::jsonb, %s)
                    """,
                    (conversation_id, sender, content, json.dumps(structured_payload or {}, ensure_ascii=False), importance_score),
                )
            conn.commit()

    def recent_messages(self, conversation_id: str, limit: int = RECENT_MESSAGE_LIMIT) -> list[dict[str, Any]]:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT sender, content, structured_payload, importance_score, created_at
                    FROM conversation_messages
                    WHERE conversation_id = %s
                    ORDER BY created_at DESC, id DESC
                    LIMIT %s
                    """,
                    (conversation_id, limit),
                )
                rows = cur.fetchall()
        output: list[dict[str, Any]] = []
        for row in reversed(rows):
            payload = row[2]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    payload = {}
            output.append(
                {
                    "sender": row[0],
                    "content": row[1],
                    "structured_payload": payload or {},
                    "importance_score": float(row[3] or 0.0),
                    "created_at": row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4]),
                }
            )
        return output

    def message_count(self, conversation_id: str) -> int:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT COUNT(*) FROM conversation_messages WHERE conversation_id = %s",
                    (conversation_id,),
                )
                row = cur.fetchone()
        return int(row[0] if row else 0)

    def append_semantic_memory(
        self,
        metadata: dict[str, Any],
        sender: str,
        content: str,
        structured_payload: dict[str, Any] | None = None,
        importance_score: float = 0.5,
    ) -> None:
        cleaned = clip_text(content, 1600)
        if not cleaned:
            return
        vector = pgvector_literal(embed_text(cleaned))
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO conversation_vector_memories(
                        conversation_id, role_scope, user_id, patient_id, visit_id, medical_record_id,
                        scene, sender, content, structured_payload, importance_score, embedding
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s::vector)
                    """,
                    (
                        metadata.get("conversation_id"),
                        metadata.get("role_scope"),
                        metadata.get("user_id"),
                        metadata.get("patient_id"),
                        metadata.get("visit_id"),
                        metadata.get("medical_record_id"),
                        metadata.get("scene"),
                        sender,
                        cleaned,
                        json.dumps(structured_payload or {}, ensure_ascii=False),
                        importance_score,
                        vector,
                    ),
                )
            conn.commit()

    def semantic_memories(self, payload: dict[str, Any], query_text: str, limit: int = SEMANTIC_MEMORY_LIMIT) -> list[dict[str, Any]]:
        conversation_id = normalize_conversation_id(payload)
        metadata = session_metadata(payload, conversation_id)
        query_vector = pgvector_literal(embed_text(query_text))
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL hnsw.ef_search = 80")
                cur.execute(
                    """
                    SELECT conversation_id, role_scope, patient_id, visit_id, medical_record_id,
                           scene, sender, content, structured_payload, importance_score, created_at,
                           1 - (embedding <=> %s::vector) AS similarity
                    FROM conversation_vector_memories
                    WHERE (
                        conversation_id = %s
                        OR (
                            role_scope = %s
                            AND patient_id IS NOT NULL
                            AND patient_id = %s
                        )
                    )
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                    """,
                    (
                        query_vector,
                        conversation_id,
                        metadata.get("role_scope"),
                        metadata.get("patient_id"),
                        query_vector,
                        limit * 3,
                    ),
                )
                rows = cur.fetchall()
        output: list[dict[str, Any]] = []
        for row in rows:
            score = float(row[11] or 0.0) * float(row[9] or 0.5)
            if score < SEMANTIC_MIN_SCORE:
                continue
            payload_value = row[8]
            if isinstance(payload_value, str):
                try:
                    payload_value = json.loads(payload_value)
                except json.JSONDecodeError:
                    payload_value = {}
            output.append(
                {
                    "conversation_id": row[0],
                    "role_scope": row[1],
                    "patient_id": row[2],
                    "visit_id": row[3],
                    "medical_record_id": row[4],
                    "scene": row[5],
                    "sender": row[6],
                    "content": row[7],
                    "structured_payload": payload_value or {},
                    "importance_score": float(row[9] or 0.0),
                    "created_at": row[10].isoformat() if hasattr(row[10], "isoformat") else str(row[10]),
                    "score": score,
                    "similarity": float(row[11] or 0.0),
                    "provider": "pgvector",
                }
            )
        return output[:limit]

    def update_memory(
        self,
        conversation_id: str,
        summary: str,
        key_facts: list[str],
        unresolved_questions: list[str],
        summarized_message_count: int | None = None,
    ) -> None:
        with db.connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE conversation_sessions
                    SET summary = %s,
                        key_facts = %s::jsonb,
                        unresolved_questions = %s::jsonb,
                        summarized_message_count = GREATEST(summarized_message_count, COALESCE(%s, summarized_message_count)),
                        last_summary_at = NOW(),
                        updated_at = NOW()
                    WHERE conversation_id = %s
                    """,
                    (
                        summary,
                        json.dumps(dedupe_texts(key_facts), ensure_ascii=False),
                        json.dumps(dedupe_texts(unresolved_questions), ensure_ascii=False),
                        summarized_message_count,
                        conversation_id,
                    ),
                )
            conn.commit()


def get_conversation_store() -> ConversationStore | None:
    if not db.is_configured():
        return None
    return PostgresConversationStore()


def build_memory_context(store: ConversationStore | None, payload: dict[str, Any], current_user_message: str) -> dict[str, Any]:
    conversation_id = normalize_conversation_id(payload)
    if not store or not conversation_id or payload.get("memory_enabled") is False:
        return {"enabled": False, "conversation_id": conversation_id, "reason": "not_configured_or_disabled"}

    session = store.upsert_session(session_metadata(payload, conversation_id))
    recent = store.recent_messages(conversation_id, RECENT_MESSAGE_LIMIT)
    message_count = store.message_count(conversation_id)
    semantic = store.semantic_memories(payload, current_user_message, SEMANTIC_MEMORY_LIMIT)
    summary = str(session.get("summary") or "")
    key_facts = list(session.get("key_facts") or [])
    unresolved = list(session.get("unresolved_questions") or [])
    summarized_message_count = int(session.get("summarized_message_count") or 0)
    return {
        "enabled": True,
        "conversation_id": conversation_id,
        "role_scope": session.get("role_scope") or payload.get("role_scope") or "unknown",
        "scene": session.get("scene") or payload.get("scene"),
        "summary": summary,
        "key_facts": key_facts,
        "unresolved_questions": unresolved,
        "recent_messages": recent,
        "recent_message_count": len(recent),
        "semantic_memories": semantic,
        "semantic_recall": {
            "enabled": True,
            "result_count": len(semantic),
            "limit": SEMANTIC_MEMORY_LIMIT,
            "scope": "conversation_or_same_patient_role",
        },
        "message_count": message_count,
        "compression": {
            "enabled": True,
            "strategy": "rolling_structured_summary",
            "summary_max_chars": SUMMARY_MAX_CHARS,
            "recent_message_limit": RECENT_MESSAGE_LIMIT,
            "compression_interval_messages": SUMMARY_COMPRESSION_MESSAGE_INTERVAL,
            "summarized_message_count": summarized_message_count,
            "has_unsummarized_messages": message_count > summarized_message_count,
        },
        "current_message_preview": clip_text(current_user_message, 180),
    }


def persist_conversation_turn(
    store: ConversationStore | None,
    payload: dict[str, Any],
    *,
    user_message: str,
    assistant_payload: dict[str, Any],
) -> None:
    conversation_id = normalize_conversation_id(payload)
    if not store or not conversation_id or payload.get("memory_enabled") is False:
        return

    session = store.upsert_session(session_metadata(payload, conversation_id))
    metadata = session_metadata(payload, conversation_id)
    store.append_message(conversation_id, "user", clip_text(user_message, 2000), {"scene": session.get("scene")}, 0.8)
    store.append_semantic_memory(metadata, "user", user_message, {"scene": session.get("scene")}, 0.9)
    assistant_text = assistant_payload_to_text(assistant_payload)
    store.append_message(conversation_id, "assistant", clip_text(assistant_text, 2000), assistant_payload, 0.6)
    store.append_semantic_memory(metadata, "assistant", assistant_text, assistant_payload, 0.45)
    message_count = store.message_count(conversation_id)
    summarized_message_count = int(session.get("summarized_message_count") or 0)
    should_compress = (
        summarized_message_count == 0
        or message_count - summarized_message_count >= SUMMARY_COMPRESSION_MESSAGE_INTERVAL
    )
    summary = str(session.get("summary") or "")
    if should_compress:
        summary = update_summary(summary, user_message, assistant_text)
        summarized_message_count = message_count
    facts = dedupe_texts(list(session.get("key_facts") or []) + extract_key_facts(user_message))
    unresolved = dedupe_texts(list(session.get("unresolved_questions") or []) + extract_unresolved_questions(user_message))
    store.update_memory(conversation_id, summary, facts, unresolved, summarized_message_count)


def normalize_conversation_id(payload: dict[str, Any]) -> str:
    value = str(payload.get("conversation_id") or "").strip()
    if value:
        return value[:160]
    return ""


def _nullable_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def session_metadata(payload: dict[str, Any], conversation_id: str) -> dict[str, Any]:
    return {
        "conversation_id": conversation_id,
        "role_scope": str(payload.get("role_scope") or "unknown")[:40],
        "user_id": str(payload.get("user_id") or "")[:80] or None,
        "patient_id": _nullable_int(payload.get("patient_id")),
        "visit_id": _nullable_int(payload.get("visit_id") or payload.get("register_id")),
        "medical_record_id": _nullable_int(payload.get("medical_record_id")),
        "scene": str(payload.get("scene") or "clinical_assist")[:80],
    }


def update_summary(previous_summary: str, user_message: str, assistant_text: str) -> str:
    parts = [part for part in [previous_summary.strip(), f"用户提到：{clip_text(user_message, 260)}", f"AI回应：{clip_text(assistant_text, 220)}"] if part]
    return clip_text("\n".join(parts), SUMMARY_MAX_CHARS)


def extract_key_facts(text: str) -> list[str]:
    facts: list[str] = []
    for fragment in re.split(r"[，,。；;\n]+", text):
        cleaned = fragment.strip()
        if not cleaned:
            continue
        if any(keyword in cleaned for keyword in FACT_KEYWORDS):
            facts.append(clip_text(cleaned, 120))
    return dedupe_texts(facts)


def semantic_tokens(text: str) -> set[str]:
    tokens = {token for token in re.findall(r"[\w\u4e00-\u9fff]+", str(text).lower()) if len(token) >= 2}
    expanded = set(tokens)
    for token in tokens:
        expanded.update(SEMANTIC_SYNONYMS.get(token, set()))
    return expanded


def lexical_semantic_score(query_tokens: set[str], content: str) -> float:
    content_tokens = semantic_tokens(content)
    if not query_tokens or not content_tokens:
        return 0.0
    overlap = query_tokens & content_tokens
    if not overlap:
        return 0.0
    return len(overlap) / max(1, min(len(query_tokens), len(content_tokens)))


def is_same_memory_scope(current: dict[str, Any], item: dict[str, Any]) -> bool:
    if current.get("conversation_id") and current.get("conversation_id") == item.get("conversation_id"):
        return True
    return (
        bool(current.get("patient_id"))
        and current.get("patient_id") == item.get("patient_id")
        and current.get("role_scope") == item.get("role_scope")
    )


def extract_unresolved_questions(text: str) -> list[str]:
    return [clip_text(item.strip(), 160) for item in re.split(r"[？?]", text) if item.strip().endswith(("吗", "么", "如何", "怎么办"))]


def assistant_payload_to_text(payload: dict[str, Any]) -> str:
    if "diagnosis_hint" in payload:
        return str(payload.get("diagnosis_hint") or "")
    if "recommendations" in payload:
        names = [str(item.get("dept_name") or item.get("deptName") or "") for item in payload.get("recommendations") or [] if isinstance(item, dict)]
        return "推荐科室：" + "、".join(name for name in names if name)
    if "suggestions" in payload:
        names = [str(item.get("disease_name") or item.get("diseaseName") or "") for item in payload.get("suggestions") or [] if isinstance(item, dict)]
        return "辅助诊断建议：" + "、".join(name for name in names if name)
    return json.dumps(payload, ensure_ascii=False)


def dedupe_texts(items: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for item in items:
        cleaned = str(item).strip()
        if cleaned and cleaned not in seen:
            seen.add(cleaned)
            output.append(cleaned)
    return output


def clip_text(text: str, max_chars: int) -> str:
    cleaned = str(text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max_chars - 1] + "…"
