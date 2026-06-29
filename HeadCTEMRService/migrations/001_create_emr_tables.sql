CREATE TABLE IF NOT EXISTS emr_diagnostic_reports (
    id UUID PRIMARY KEY,
    document_id VARCHAR(128) NOT NULL UNIQUE,
    idempotency_key VARCHAR(256) NOT NULL UNIQUE,
    source_report_id UUID NOT NULL UNIQUE,
    order_id VARCHAR(128) NOT NULL,
    study_id VARCHAR(128) NOT NULL,
    accession_number VARCHAR(128),
    patient_id VARCHAR(128) NOT NULL,
    department VARCHAR(128),
    status VARCHAR(32) NOT NULL DEFAULT 'final',
    findings TEXT NOT NULL,
    impression TEXT NOT NULL,
    recommendations TEXT NOT NULL DEFAULT '',
    signed_by VARCHAR(128) NOT NULL,
    signed_at TIMESTAMPTZ NOT NULL,
    released_at TIMESTAMPTZ,
    content_hash VARCHAR(64) NOT NULL,
    source_payload JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS emr_audit_events (
    id BIGSERIAL PRIMARY KEY,
    action VARCHAR(64) NOT NULL,
    document_id VARCHAR(128) NOT NULL,
    source_report_id UUID NOT NULL,
    request_id VARCHAR(128),
    client_ip VARCHAR(128),
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emr_reports_patient ON emr_diagnostic_reports(patient_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_emr_reports_study ON emr_diagnostic_reports(study_id);
CREATE INDEX IF NOT EXISTS idx_emr_audit_document ON emr_audit_events(document_id, created_at DESC);

