-- Project2 core HIS schema for PostgreSQL.
-- This file is the formal database initialization entrypoint.

CREATE TABLE IF NOT EXISTS department (
    id SERIAL PRIMARY KEY,
    dept_code VARCHAR(64),
    dept_name VARCHAR(128),
    dept_type VARCHAR(64),
    delmark BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS regist_level (
    id SERIAL PRIMARY KEY,
    regist_code VARCHAR(64),
    regist_name VARCHAR(128),
    regist_fee NUMERIC(12,2),
    regist_quota INTEGER,
    is_expert BOOLEAN DEFAULT FALSE,
    sequence_no INTEGER,
    delmark BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settle_category (
    id SERIAL PRIMARY KEY,
    settle_code VARCHAR(64),
    settle_name VARCHAR(128),
    sequence_no INTEGER,
    delmark BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employee (
    id SERIAL PRIMARY KEY,
    deptment_id INTEGER REFERENCES department(id),
    regist_level_id INTEGER REFERENCES regist_level(id),
    realname VARCHAR(128),
    role_type VARCHAR(64),
    title_level VARCHAR(64),
    password_hash VARCHAR(256),
    phone VARCHAR(64),
    email VARCHAR(128),
    delmark BOOLEAN DEFAULT TRUE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scheduling (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employee(id),
    deptment_id INTEGER REFERENCES department(id),
    schedule_date DATE,
    noon VARCHAR(16),
    regist_quota INTEGER,
    schedule_status VARCHAR(32),
    source_type VARCHAR(32),
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS patient (
    id SERIAL PRIMARY KEY,
    case_number VARCHAR(64),
    real_name VARCHAR(128),
    gender VARCHAR(16),
    card_number VARCHAR(64),
    birthdate DATE,
    phone VARCHAR(64),
    home_address TEXT,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS register (
    id SERIAL PRIMARY KEY,
    visit_no VARCHAR(64),
    patient_id INTEGER REFERENCES patient(id),
    visit_date DATE,
    noon VARCHAR(16),
    deptment_id INTEGER REFERENCES department(id),
    employee_id INTEGER REFERENCES employee(id),
    regist_level_id INTEGER REFERENCES regist_level(id),
    settle_category_id INTEGER REFERENCES settle_category(id),
    source_type VARCHAR(32),
    queue_no INTEGER,
    regist_method VARCHAR(32),
    regist_money NUMERIC(12,2),
    visit_state VARCHAR(32),
    cancel_reason TEXT,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medical_record (
    id SERIAL PRIMARY KEY,
    register_id INTEGER REFERENCES register(id),
    doctor_id INTEGER REFERENCES employee(id),
    readme TEXT,
    present TEXT,
    present_treat TEXT,
    history TEXT,
    allergy TEXT,
    physique TEXT,
    proposal TEXT,
    careful TEXT,
    diagnosis TEXT,
    cure TEXT,
    record_status VARCHAR(32),
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS disease (
    id SERIAL PRIMARY KEY,
    disease_code VARCHAR(64),
    disease_name VARCHAR(128),
    disease_type VARCHAR(64),
    icd_code VARCHAR(64),
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS medical_record_disease (
    medical_record_id INTEGER REFERENCES medical_record(id),
    disease_id INTEGER REFERENCES disease(id)
);

CREATE TABLE IF NOT EXISTS medical_technology (
    id SERIAL PRIMARY KEY,
    tech_code VARCHAR(64),
    tech_name VARCHAR(128),
    tech_format VARCHAR(128),
    tech_price NUMERIC(12,2),
    tech_type VARCHAR(64),
    price_type VARCHAR(64),
    deptment_id INTEGER REFERENCES department(id),
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS check_request (
    id SERIAL PRIMARY KEY,
    register_id INTEGER REFERENCES register(id),
    medical_technology_id INTEGER REFERENCES medical_technology(id),
    check_info TEXT,
    check_position VARCHAR(128),
    creation_time TIMESTAMP DEFAULT NOW(),
    check_employee_id INTEGER,
    inputcheck_employee_id INTEGER,
    check_time TIMESTAMP,
    check_result TEXT,
    check_state VARCHAR(32),
    check_remark TEXT
);

CREATE TABLE IF NOT EXISTS inspection_request (
    id SERIAL PRIMARY KEY,
    register_id INTEGER REFERENCES register(id),
    medical_technology_id INTEGER REFERENCES medical_technology(id),
    inspection_info TEXT,
    inspection_position VARCHAR(128),
    creation_time TIMESTAMP DEFAULT NOW(),
    inspection_employee_id INTEGER,
    inputinspection_employee_id INTEGER,
    inspection_time TIMESTAMP,
    inspection_result TEXT,
    inspection_state VARCHAR(32),
    inspection_remark TEXT
);

CREATE TABLE IF NOT EXISTS disposal_request (
    id SERIAL PRIMARY KEY,
    register_id INTEGER REFERENCES register(id),
    medical_technology_id INTEGER REFERENCES medical_technology(id),
    disposal_info TEXT,
    disposal_position VARCHAR(128),
    creation_time TIMESTAMP DEFAULT NOW(),
    disposal_employee_id INTEGER,
    inputdisposal_employee_id INTEGER,
    disposal_time TIMESTAMP,
    disposal_result TEXT,
    disposal_state VARCHAR(32),
    disposal_remark TEXT
);

CREATE TABLE IF NOT EXISTS drug_info (
    id SERIAL PRIMARY KEY,
    drug_code VARCHAR(64),
    drug_name VARCHAR(128),
    drug_format VARCHAR(128),
    drug_unit VARCHAR(64),
    manufacturer VARCHAR(128),
    drug_dosage VARCHAR(64),
    drug_type VARCHAR(64),
    drug_price NUMERIC(12,2),
    stock_num INTEGER,
    mnemonic_code VARCHAR(64),
    creation_date DATE DEFAULT CURRENT_DATE,
    create_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS drug_stock_record (
    id SERIAL PRIMARY KEY,
    drug_id INTEGER REFERENCES drug_info(id),
    record_type VARCHAR(32) NOT NULL,
    quantity INTEGER NOT NULL,
    before_stock INTEGER NOT NULL,
    after_stock INTEGER NOT NULL,
    operator_id INTEGER REFERENCES employee(id),
    related_prescription_id INTEGER,
    reason TEXT,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS prescription (
    id SERIAL PRIMARY KEY,
    register_id INTEGER REFERENCES register(id),
    doctor_id INTEGER REFERENCES employee(id),
    prescription_no VARCHAR(64),
    total_amount NUMERIC(12,2),
    prescription_status VARCHAR(32),
    creation_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW(),
    dispense_time TIMESTAMP,
    pharmacist_id INTEGER REFERENCES employee(id)
);

CREATE TABLE IF NOT EXISTS prescription_detail (
    id SERIAL PRIMARY KEY,
    prescription_id INTEGER REFERENCES prescription(id),
    drug_id INTEGER REFERENCES drug_info(id),
    usage_route VARCHAR(128),
    frequency VARCHAR(128),
    single_dose VARCHAR(128),
    use_days INTEGER,
    drug_number INTEGER
);

CREATE TABLE IF NOT EXISTS finance_record (
    id SERIAL PRIMARY KEY,
    record_no VARCHAR(96),
    register_id INTEGER REFERENCES register(id),
    item_id INTEGER,
    item_type VARCHAR(32),
    item_name VARCHAR(128),
    amount NUMERIC(12,2),
    charge_method VARCHAR(32),
    record_type VARCHAR(32),
    operator_name VARCHAR(128),
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_consultation (
    id SERIAL PRIMARY KEY,
    patient_id INTEGER,
    register_id INTEGER,
    symptoms_desc TEXT,
    ai_recommend_dept TEXT,
    ai_diagnosis_hint TEXT,
    consultation_time TIMESTAMP DEFAULT NOW(),
    ai_model_version VARCHAR(128),
    status SMALLINT DEFAULT 1,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_diagnosis_suggestion (
    id SERIAL PRIMARY KEY,
    medical_record_id INTEGER,
    register_id INTEGER,
    ai_diagnosis TEXT,
    disease_id INTEGER,
    confidence NUMERIC(10,6),
    evidence_basis TEXT,
    doctor_feedback TEXT,
    suggestion_time TIMESTAMP DEFAULT NOW(),
    ai_model_version VARCHAR(128),
    is_adopted BOOLEAN DEFAULT FALSE,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_image_file (
    id SERIAL PRIMARY KEY,
    check_request_id INTEGER,
    register_id INTEGER,
    file_path TEXT,
    file_name VARCHAR(255),
    file_size BIGINT,
    file_format VARCHAR(64),
    upload_time TIMESTAMP DEFAULT NOW(),
    upload_by INTEGER,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_image_analysis (
    id SERIAL PRIMARY KEY,
    check_request_id INTEGER,
    register_id INTEGER,
    file_path TEXT,
    ai_findings TEXT,
    ai_annotation TEXT,
    ai_conclusion TEXT,
    confidence NUMERIC(10,6),
    analysis_time TIMESTAMP DEFAULT NOW(),
    ai_model_version VARCHAR(128),
    is_reviewed SMALLINT DEFAULT 0,
    reviewed_by INTEGER,
    reviewed_time TIMESTAMP,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_generated_report (
    id SERIAL PRIMARY KEY,
    request_id INTEGER,
    register_id INTEGER,
    report_type VARCHAR(64),
    ai_raw_content TEXT,
    ai_structured_data TEXT,
    final_content TEXT,
    reference_source VARCHAR(128),
    ai_model_version VARCHAR(128),
    generation_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(32),
    is_confirmed SMALLINT DEFAULT 0,
    confirmed_by INTEGER,
    confirmed_time TIMESTAMP,
    edit_history TEXT,
    create_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_schedule_rule (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(128),
    deptment_id INTEGER REFERENCES department(id),
    rule_config TEXT,
    constraint_json TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    ai_model_version VARCHAR(128),
    created_time TIMESTAMP DEFAULT NOW(),
    updated_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ai_schedule_result (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER REFERENCES employee(id),
    deptment_id INTEGER REFERENCES department(id),
    schedule_date DATE,
    shift_type VARCHAR(32),
    regist_quota INTEGER,
    is_generated SMALLINT DEFAULT 1,
    is_modified SMALLINT DEFAULT 0,
    source_type VARCHAR(32),
    created_time TIMESTAMP DEFAULT NOW(),
    update_time TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_register_patient_id ON register(patient_id);
CREATE INDEX IF NOT EXISTS idx_register_employee_state ON register(employee_id, visit_state);
CREATE INDEX IF NOT EXISTS idx_scheduling_dept_date_noon ON scheduling(deptment_id, schedule_date, noon);
CREATE INDEX IF NOT EXISTS idx_medical_record_register_id ON medical_record(register_id);
CREATE INDEX IF NOT EXISTS idx_check_request_register_id ON check_request(register_id);
CREATE INDEX IF NOT EXISTS idx_inspection_request_register_id ON inspection_request(register_id);
CREATE INDEX IF NOT EXISTS idx_disposal_request_register_id ON disposal_request(register_id);
CREATE INDEX IF NOT EXISTS idx_prescription_register_id ON prescription(register_id);
CREATE INDEX IF NOT EXISTS idx_finance_record_create_time ON finance_record(create_time);
CREATE INDEX IF NOT EXISTS idx_finance_record_register_id ON finance_record(register_id);
CREATE INDEX IF NOT EXISTS idx_drug_stock_record_drug_id ON drug_stock_record(drug_id);
CREATE INDEX IF NOT EXISTS idx_drug_stock_record_create_time ON drug_stock_record(create_time);
CREATE INDEX IF NOT EXISTS idx_ai_image_analysis_check_request_id ON ai_image_analysis(check_request_id);
CREATE INDEX IF NOT EXISTS idx_ai_generated_report_request_id ON ai_generated_report(request_id);

DO $$
DECLARE
    demo_dept_id INTEGER;
    demo_level_id INTEGER;
    demo_settle_id INTEGER;
    demo_doctor_id INTEGER;
    demo_admin_id INTEGER;
    demo_medical_tech_id INTEGER;
    demo_pharmacist_id INTEGER;
    demo_patient_id INTEGER;
BEGIN
    SELECT id INTO demo_dept_id FROM department WHERE dept_code = 'DEMO-NEURO' ORDER BY id LIMIT 1;
    IF demo_dept_id IS NULL THEN
        INSERT INTO department(dept_code, dept_name, dept_type, delmark)
        VALUES ('DEMO-NEURO', '神经外科', 'CLINICAL', TRUE)
        RETURNING id INTO demo_dept_id;
    END IF;

    SELECT id INTO demo_level_id FROM regist_level WHERE regist_code = 'DEMO-NORMAL' ORDER BY id LIMIT 1;
    IF demo_level_id IS NULL THEN
        INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
        VALUES ('DEMO-NORMAL', '普通号', 20.00, 50, FALSE, 1, TRUE)
        RETURNING id INTO demo_level_id;
    END IF;

    SELECT id INTO demo_settle_id FROM settle_category WHERE settle_code = 'DEMO-SELF' ORDER BY id LIMIT 1;
    IF demo_settle_id IS NULL THEN
        INSERT INTO settle_category(settle_code, settle_name, sequence_no, delmark)
        VALUES ('DEMO-SELF', '自费', 1, TRUE)
        RETURNING id INTO demo_settle_id;
    END IF;

    SELECT id INTO demo_doctor_id FROM employee WHERE realname = 'doctor' ORDER BY id LIMIT 1;
    IF demo_doctor_id IS NULL THEN
        INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, delmark)
        VALUES (demo_dept_id, demo_level_id, 'doctor', 'DOCTOR', '主治医师', '123456', '13900000001', TRUE)
        RETURNING id INTO demo_doctor_id;
    ELSE
        UPDATE employee
        SET deptment_id = demo_dept_id,
            regist_level_id = demo_level_id,
            role_type = 'DOCTOR',
            title_level = COALESCE(title_level, '主治医师'),
            password_hash = '123456',
            phone = COALESCE(phone, '13900000001'),
            delmark = TRUE
        WHERE id = demo_doctor_id;
    END IF;

    SELECT id INTO demo_admin_id FROM employee WHERE realname = 'admin' ORDER BY id LIMIT 1;
    IF demo_admin_id IS NULL THEN
        INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
        VALUES (demo_dept_id, 'admin', 'ADMIN', '管理员', '123456', '13900000002', TRUE)
        RETURNING id INTO demo_admin_id;
    ELSE
        UPDATE employee
        SET deptment_id = demo_dept_id,
            role_type = 'ADMIN',
            title_level = COALESCE(title_level, '管理员'),
            password_hash = '123456',
            phone = COALESCE(phone, '13900000002'),
            delmark = TRUE
        WHERE id = demo_admin_id;
    END IF;

    SELECT id INTO demo_medical_tech_id FROM employee WHERE realname = 'medicaltech' ORDER BY id LIMIT 1;
    IF demo_medical_tech_id IS NULL THEN
        INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
        VALUES (demo_dept_id, 'medicaltech', 'MEDICAL_TECH', '技师', '123456', '13900000003', TRUE)
        RETURNING id INTO demo_medical_tech_id;
    ELSE
        UPDATE employee
        SET deptment_id = demo_dept_id,
            role_type = 'MEDICAL_TECH',
            title_level = COALESCE(title_level, '技师'),
            password_hash = '123456',
            phone = COALESCE(phone, '13900000003'),
            delmark = TRUE
        WHERE id = demo_medical_tech_id;
    END IF;

    SELECT id INTO demo_pharmacist_id FROM employee WHERE realname = 'pharmacist' ORDER BY id LIMIT 1;
    IF demo_pharmacist_id IS NULL THEN
        INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, delmark)
        VALUES (demo_dept_id, 'pharmacist', 'PHARMACIST', '药师', '123456', '13900000004', TRUE)
        RETURNING id INTO demo_pharmacist_id;
    ELSE
        UPDATE employee
        SET deptment_id = demo_dept_id,
            role_type = 'PHARMACIST',
            title_level = COALESCE(title_level, '药师'),
            password_hash = '123456',
            phone = COALESCE(phone, '13900000004'),
            delmark = TRUE
        WHERE id = demo_pharmacist_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM scheduling
        WHERE employee_id = demo_doctor_id
          AND deptment_id = demo_dept_id
          AND schedule_date = CURRENT_DATE
          AND noon = 'AM'
    ) THEN
        INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
        VALUES (demo_doctor_id, demo_dept_id, CURRENT_DATE, 'AM', 50, 'NORMAL', 'DEMO');
    END IF;

    SELECT id INTO demo_patient_id FROM patient WHERE card_number = 'DEMO-PATIENT-001' ORDER BY id LIMIT 1;
    IF demo_patient_id IS NULL THEN
        INSERT INTO patient(case_number, real_name, gender, card_number, birthdate, phone, home_address)
        VALUES ('DEMO-CASE-001', '演示患者', 'M', 'DEMO-PATIENT-001', DATE '1988-01-01', '13800009999', '演示地址')
        RETURNING id INTO demo_patient_id;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM register
        WHERE patient_id = demo_patient_id
          AND employee_id = demo_doctor_id
          AND visit_date = CURRENT_DATE
          AND visit_state IN ('REGISTERED', 'DOCTOR_RECEIVED')
    ) THEN
        INSERT INTO register(
            visit_no, patient_id, visit_date, noon, deptment_id, employee_id,
            regist_level_id, settle_category_id, source_type, queue_no, regist_method, regist_money, visit_state
        )
        VALUES (
            'DEMO-' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' || demo_patient_id,
            demo_patient_id, CURRENT_DATE, 'AM', demo_dept_id, demo_doctor_id,
            demo_level_id, demo_settle_id, 'DEMO', 1, 'WINDOW', 20.00, 'REGISTERED'
        );
    END IF;
END $$;
