from __future__ import annotations

from HeadCTOrchestrator.conversation.memory_service import (
    InMemoryConversationStore,
    build_memory_context,
    persist_conversation_turn,
)
from HeadCTOrchestrator.rag import clinical_assist


def test_conversation_memory_keeps_recent_turns_and_summary() -> None:
    store = InMemoryConversationStore()
    payload = {
        "conversation_id": "patient-12-consultation",
        "role_scope": "patient",
        "user_id": "patient-12",
        "patient_id": 12,
        "visit_id": 88,
        "scene": "consultation",
    }

    empty_context = build_memory_context(store, payload, "最近头痛加重")

    assert empty_context["enabled"] is True
    assert empty_context["conversation_id"] == "patient-12-consultation"
    assert empty_context["recent_message_count"] == 0

    persist_conversation_turn(
        store,
        payload,
        user_message="头痛持续3天，伴恶心，高血压病史。",
        assistant_payload={"diagnosis_hint": "建议神经内科进一步评估。"},
    )

    context = build_memory_context(store, payload, "现在头痛比早上更明显")

    assert context["enabled"] is True
    assert context["recent_message_count"] == 2
    assert "头痛持续3天" in context["summary"]
    assert "高血压病史" in context["key_facts"]
    assert context["recent_messages"][0]["sender"] == "user"
    assert context["recent_messages"][1]["sender"] == "assistant"


def test_conversation_memory_isolated_by_conversation_id() -> None:
    store = InMemoryConversationStore()
    first_payload = {
        "conversation_id": "patient-12-consultation",
        "role_scope": "patient",
        "patient_id": 12,
        "scene": "consultation",
    }
    second_payload = {
        "conversation_id": "patient-13-consultation",
        "role_scope": "patient",
        "patient_id": 13,
        "scene": "consultation",
    }

    persist_conversation_turn(
        store,
        first_payload,
        user_message="患者12提到夜间头痛。",
        assistant_payload={"diagnosis_hint": "建议复核。"},
    )

    context = build_memory_context(store, second_payload, "我也头痛")

    assert context["enabled"] is True
    assert context["recent_message_count"] == 0
    assert "患者12" not in context["summary"]


def test_clinical_consultation_injects_previous_turn_memory(monkeypatch) -> None:
    store = InMemoryConversationStore()
    captured_prompts: list[dict] = []

    monkeypatch.setattr(
        clinical_assist,
        "_retrieve",
        lambda query_text: {
            "status": "success",
            "retrieval_confidence": 0.8,
            "sources": [],
            "snippets": [],
            "cache_hit": False,
        },
    )
    monkeypatch.setattr(clinical_assist, "get_conversation_store", lambda: store, raising=False)

    def fake_call_bailian_cached(*, cache_kind: str, prompt_payload: dict, messages: list[dict]):
        captured_prompts.append(prompt_payload)
        return (
            {
                "recommendations": [
                    {"dept_id": 1, "dept_name": "神经内科", "confidence": 0.72, "reason": "头痛需要进一步评估。"}
                ],
                "diagnosis_hint": "AI辅助问诊结果仅供医生参考，最终结论需医生审核。",
            },
            False,
            "disabled",
        )

    monkeypatch.setattr(clinical_assist, "_call_bailian_cached", fake_call_bailian_cached)

    first = clinical_assist.generate_consultation_assist(
        {
            "conversation_id": "patient-12-consultation",
            "role_scope": "patient",
            "user_id": "patient-12",
            "patient_id": 12,
            "symptoms": "头痛持续3天，伴恶心，高血压病史。",
        }
    )
    second = clinical_assist.generate_consultation_assist(
        {
            "conversation_id": "patient-12-consultation",
            "role_scope": "patient",
            "user_id": "patient-12",
            "patient_id": 12,
            "symptoms": "现在头痛比早上更明显，需要挂什么科？",
        }
    )

    assert first["memory_context"]["recent_message_count"] == 0
    assert second["memory_context"]["recent_message_count"] == 2
    assert "头痛持续3天" in captured_prompts[1]["conversation_memory"]["summary"]
    assert "高血压病史" in captured_prompts[1]["conversation_memory"]["key_facts"]


def test_conversation_memory_periodically_compresses_long_context() -> None:
    store = InMemoryConversationStore()
    payload = {
        "conversation_id": "patient-12-long-context",
        "role_scope": "patient",
        "patient_id": 12,
        "scene": "consultation",
    }

    for index in range(7):
        message = f"第{index + 1}轮：头痛持续3天，高血压病史，夜间加重。"
        persist_conversation_turn(
            store,
            payload,
            user_message=message,
            assistant_payload={"diagnosis_hint": f"第{index + 1}轮建议继续补充病史。"},
        )

    context = build_memory_context(store, payload, "还记得我之前说的高血压病史吗？")

    assert context["message_count"] == 14
    assert context["recent_message_count"] == 8
    assert context["compression"]["enabled"] is True
    assert context["compression"]["strategy"] == "rolling_structured_summary"
    assert context["compression"]["summarized_message_count"] >= 12
    assert "高血压病史" in context["summary"]
    assert any("高血压病史" in fact for fact in context["key_facts"])


def test_conversation_memory_semantic_recall_finds_old_relevant_context() -> None:
    store = InMemoryConversationStore()
    payload = {
        "conversation_id": "patient-12-semantic-a",
        "role_scope": "patient",
        "patient_id": 12,
        "scene": "consultation",
    }

    persist_conversation_turn(
        store,
        payload,
        user_message="I take warfarin every night after atrial fibrillation treatment.",
        assistant_payload={"diagnosis_hint": "Please tell the doctor about anticoagulant medicine."},
    )
    for index in range(10):
        persist_conversation_turn(
            store,
            payload,
            user_message=f"Routine follow up message {index}: sleep and appetite are stable.",
            assistant_payload={"diagnosis_hint": "Continue routine observation."},
        )

    context = build_memory_context(
        store,
        payload,
        "Do you remember the anticoagulant medicine I mentioned before?",
    )

    assert context["recent_message_count"] == 8
    assert all("warfarin" not in message["content"].lower() for message in context["recent_messages"])
    assert context["semantic_recall"]["enabled"] is True
    assert context["semantic_recall"]["result_count"] >= 1
    assert any("warfarin" in item["content"].lower() for item in context["semantic_memories"])


def test_conversation_memory_semantic_recall_can_cross_sessions_for_same_patient() -> None:
    store = InMemoryConversationStore()
    first_payload = {
        "conversation_id": "patient-12-old-session",
        "role_scope": "patient",
        "patient_id": 12,
        "scene": "consultation",
    }
    second_payload = {
        "conversation_id": "patient-12-new-session",
        "role_scope": "patient",
        "patient_id": 12,
        "scene": "consultation",
    }

    persist_conversation_turn(
        store,
        first_payload,
        user_message="Previous visit: contrast allergy was reported before CT examination.",
        assistant_payload={"diagnosis_hint": "Record contrast allergy for future imaging review."},
    )

    context = build_memory_context(
        store,
        second_payload,
        "Was there any allergy mentioned in earlier conversations?",
    )

    assert context["recent_message_count"] == 0
    assert any("contrast allergy" in item["content"].lower() for item in context["semantic_memories"])
