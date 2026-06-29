CREATE INDEX IF NOT EXISTS idx_examination_orders_status ON examination_orders(status, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_medical_reports_status ON medical_reports(status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_medical_reports_assigned ON medical_reports(assigned_doctor_id, status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_versions_report ON medical_report_versions(report_id, version_number DESC);
CREATE INDEX IF NOT EXISTS idx_report_reviews_report ON report_reviews(report_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_audit_target ON report_audit_events(target_type, target_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_outbox_pending ON report_outbox_events(status, next_attempt_at);

