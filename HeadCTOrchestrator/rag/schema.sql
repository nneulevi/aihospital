CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS rag_documents (
    id BIGSERIAL PRIMARY KEY,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    tags TEXT[] NOT NULL DEFAULT '{}',
    version TEXT NOT NULL DEFAULT 'v1',
    language TEXT NOT NULL DEFAULT 'zh-CN',
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_rag_documents_source_hash
ON rag_documents(source_id, content_hash);

CREATE INDEX IF NOT EXISTS idx_rag_documents_tags
ON rag_documents USING GIN(tags);

CREATE INDEX IF NOT EXISTS idx_rag_documents_metadata
ON rag_documents USING GIN(metadata);

DROP INDEX IF EXISTS idx_rag_documents_embedding;

CREATE INDEX IF NOT EXISTS idx_rag_documents_embedding_hnsw
ON rag_documents USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE TABLE IF NOT EXISTS conversation_sessions (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL UNIQUE,
    role_scope TEXT NOT NULL DEFAULT 'unknown',
    user_id TEXT,
    patient_id BIGINT,
    visit_id BIGINT,
    medical_record_id BIGINT,
    scene TEXT NOT NULL DEFAULT 'clinical_assist',
    summary TEXT NOT NULL DEFAULT '',
    key_facts JSONB NOT NULL DEFAULT '[]'::jsonb,
    unresolved_questions JSONB NOT NULL DEFAULT '[]'::jsonb,
    summarized_message_count INTEGER NOT NULL DEFAULT 0,
    last_summary_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE conversation_sessions
ADD COLUMN IF NOT EXISTS summarized_message_count INTEGER NOT NULL DEFAULT 0;

ALTER TABLE conversation_sessions
ADD COLUMN IF NOT EXISTS last_summary_at TIMESTAMPTZ;

CREATE INDEX IF NOT EXISTS idx_conversation_sessions_scope_patient
ON conversation_sessions(role_scope, patient_id, visit_id, medical_record_id);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversation_sessions(conversation_id) ON DELETE CASCADE,
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    structured_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_conversation_created
ON conversation_messages(conversation_id, created_at DESC);

CREATE TABLE IF NOT EXISTS conversation_vector_memories (
    id BIGSERIAL PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversation_sessions(conversation_id) ON DELETE CASCADE,
    role_scope TEXT NOT NULL DEFAULT 'unknown',
    user_id TEXT,
    patient_id BIGINT,
    visit_id BIGINT,
    medical_record_id BIGINT,
    scene TEXT NOT NULL DEFAULT 'clinical_assist',
    sender TEXT NOT NULL,
    content TEXT NOT NULL,
    structured_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    importance_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
    embedding vector(1536) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_vector_scope
ON conversation_vector_memories(role_scope, patient_id, visit_id, medical_record_id);

CREATE INDEX IF NOT EXISTS idx_conversation_vector_conversation
ON conversation_vector_memories(conversation_id, created_at DESC);

DROP INDEX IF EXISTS idx_conversation_vector_embedding;

CREATE INDEX IF NOT EXISTS idx_conversation_vector_embedding_hnsw
ON conversation_vector_memories USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
