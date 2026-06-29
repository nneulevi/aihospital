CREATE TABLE IF NOT EXISTS examination_orders (
    id UUID PRIMARY KEY,
    order_id VARCHAR(128) NOT NULL UNIQUE,
    study_id VARCHAR(128) NOT NULL UNIQUE,
    accession_number VARCHAR(128),
    patient_id VARCHAR(128) NOT NULL,
    patient_name VARCHAR(128),
    department VARCHAR(128),
    ordering_doctor_id VARCHAR(128),
    study_instance_uid VARCHAR(256),
    status VARCHAR(32) NOT NULL DEFAULT 'ordered',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_analysis_snapshots (
    id UUID PRIMARY KEY,
    examination_order_id UUID NOT NULL REFERENCES examination_orders(id),
    orchestrator_task_id VARCHAR(128) NOT NULL UNIQUE,
    pipeline_version VARCHAR(64),
    model_versions JSONB NOT NULL DEFAULT '{}'::jsonb,
    quality_control_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    lesion_analysis_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    report_assist_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    rag_references_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    source_result_hash VARCHAR(64) NOT NULL,
    deployment_mode VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medical_reports (
    id UUID PRIMARY KEY,
    examination_order_id UUID NOT NULL UNIQUE REFERENCES examination_orders(id),
    ai_snapshot_id UUID NOT NULL UNIQUE REFERENCES ai_analysis_snapshots(id),
    current_version_id UUID,
    status VARCHAR(32) NOT NULL DEFAULT 'draft',
    version_lock INTEGER NOT NULL DEFAULT 1,
    idempotency_key VARCHAR(256) UNIQUE,
    assigned_doctor_id VARCHAR(128),
    reviewer_doctor_id VARCHAR(128),
    signed_by VARCHAR(128),
    signed_at TIMESTAMPTZ,
    released_at TIMESTAMPTZ,
    external_document_id VARCHAR(256),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medical_report_versions (
    id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES medical_reports(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    findings TEXT NOT NULL,
    impression TEXT NOT NULL,
    recommendations TEXT NOT NULL DEFAULT '',
    editor_id VARCHAR(128) NOT NULL,
    change_reason TEXT,
    source_type VARCHAR(32) NOT NULL,
    content_hash VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(report_id, version_number)
);

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'medical_reports_current_version_fk'
    ) THEN
        ALTER TABLE medical_reports
            ADD CONSTRAINT medical_reports_current_version_fk
            FOREIGN KEY (current_version_id) REFERENCES medical_report_versions(id);
    END IF;
END $$;

CREATE TABLE IF NOT EXISTS report_reviews (
    id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES medical_reports(id) ON DELETE CASCADE,
    report_version_id UUID NOT NULL REFERENCES medical_report_versions(id),
    reviewer_id VARCHAR(128) NOT NULL,
    decision VARCHAR(32) NOT NULL,
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_audit_events (
    id BIGSERIAL PRIMARY KEY,
    actor_id VARCHAR(128) NOT NULL,
    actor_role VARCHAR(64) NOT NULL,
    action VARCHAR(64) NOT NULL,
    target_type VARCHAR(64) NOT NULL,
    target_id VARCHAR(128) NOT NULL,
    request_id VARCHAR(128),
    client_ip VARCHAR(128),
    before_hash VARCHAR(64),
    after_hash VARCHAR(64),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS report_outbox_events (
    id UUID PRIMARY KEY,
    report_id UUID NOT NULL REFERENCES medical_reports(id) ON DELETE CASCADE,
    event_type VARCHAR(64) NOT NULL,
    payload_json JSONB NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    next_attempt_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_error TEXT,
    external_document_id VARCHAR(256),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    delivered_at TIMESTAMPTZ,
    UNIQUE(report_id, event_type)
);

