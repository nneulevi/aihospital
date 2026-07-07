-- Project2 realistic business seed data.
-- Idempotent: safe to run multiple times on a local demo database.

DO $$
DECLARE
    normal_level_id INTEGER;
    expert_level_id INTEGER;
    self_pay_id INTEGER;
    neuro_dept_id INTEGER;
    imaging_dept_id INTEGER;
    emergency_dept_id INTEGER;
    pharmacy_dept_id INTEGER;
    neuro_doctor_id INTEGER;
    emergency_doctor_id INTEGER;
    imaging_tech_id INTEGER;
    pharmacist_id INTEGER;
    seeded_drug_id INTEGER;
    target_date DATE;
BEGIN
    SELECT id INTO normal_level_id FROM regist_level WHERE regist_code = 'BIZ-NORMAL' ORDER BY id LIMIT 1;
    IF normal_level_id IS NULL THEN
        INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
        VALUES ('BIZ-NORMAL', '普通门诊', 20.00, 40, FALSE, 10, TRUE)
        RETURNING id INTO normal_level_id;
    END IF;

    SELECT id INTO expert_level_id FROM regist_level WHERE regist_code = 'BIZ-EXPERT' ORDER BY id LIMIT 1;
    IF expert_level_id IS NULL THEN
        INSERT INTO regist_level(regist_code, regist_name, regist_fee, regist_quota, is_expert, sequence_no, delmark)
        VALUES ('BIZ-EXPERT', '专家门诊', 50.00, 20, TRUE, 20, TRUE)
        RETURNING id INTO expert_level_id;
    END IF;

    SELECT id INTO self_pay_id FROM settle_category WHERE settle_code = 'BIZ-SELF' ORDER BY id LIMIT 1;
    IF self_pay_id IS NULL THEN
        INSERT INTO settle_category(settle_code, settle_name, sequence_no, delmark)
        VALUES ('BIZ-SELF', '自费', 10, TRUE)
        RETURNING id INTO self_pay_id;
    END IF;

    SELECT id INTO neuro_dept_id FROM department WHERE dept_code = 'BIZ-NEURO' ORDER BY id LIMIT 1;
    IF neuro_dept_id IS NULL THEN
        INSERT INTO department(dept_code, dept_name, dept_type, delmark)
        VALUES ('BIZ-NEURO', '神经内科', 'CLINICAL', TRUE)
        RETURNING id INTO neuro_dept_id;
    END IF;

    SELECT id INTO imaging_dept_id FROM department WHERE dept_code = 'BIZ-IMAGING' ORDER BY id LIMIT 1;
    IF imaging_dept_id IS NULL THEN
        INSERT INTO department(dept_code, dept_name, dept_type, delmark)
        VALUES ('BIZ-IMAGING', '医学影像科', 'MEDICAL_TECH', TRUE)
        RETURNING id INTO imaging_dept_id;
    END IF;

    SELECT id INTO emergency_dept_id FROM department WHERE dept_code = 'BIZ-EMERGENCY' ORDER BY id LIMIT 1;
    IF emergency_dept_id IS NULL THEN
        INSERT INTO department(dept_code, dept_name, dept_type, delmark)
        VALUES ('BIZ-EMERGENCY', '急诊科', 'CLINICAL', TRUE)
        RETURNING id INTO emergency_dept_id;
    END IF;

    SELECT id INTO pharmacy_dept_id FROM department WHERE dept_code = 'BIZ-PHARMACY' ORDER BY id LIMIT 1;
    IF pharmacy_dept_id IS NULL THEN
        INSERT INTO department(dept_code, dept_name, dept_type, delmark)
        VALUES ('BIZ-PHARMACY', '药剂科', 'PHARMACY', TRUE)
        RETURNING id INTO pharmacy_dept_id;
    END IF;

    SELECT id INTO neuro_doctor_id FROM employee WHERE phone = '13910001001' ORDER BY id LIMIT 1;
    IF neuro_doctor_id IS NULL THEN
        INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, email, delmark)
        VALUES (neuro_dept_id, expert_level_id, '赵明远', 'DOCTOR', '主任医师', '123456', '13910001001', 'zhao.neuro@example.local', TRUE)
        RETURNING id INTO neuro_doctor_id;
    ELSE
        UPDATE employee
        SET deptment_id = neuro_dept_id,
            regist_level_id = expert_level_id,
            realname = '赵明远',
            role_type = 'DOCTOR',
            title_level = '主任医师',
            password_hash = '123456',
            delmark = TRUE
        WHERE id = neuro_doctor_id;
    END IF;

    SELECT id INTO emergency_doctor_id FROM employee WHERE phone = '13910001002' ORDER BY id LIMIT 1;
    IF emergency_doctor_id IS NULL THEN
        INSERT INTO employee(deptment_id, regist_level_id, realname, role_type, title_level, password_hash, phone, email, delmark)
        VALUES (emergency_dept_id, normal_level_id, '李静', 'DOCTOR', '主治医师', '123456', '13910001002', 'li.emergency@example.local', TRUE)
        RETURNING id INTO emergency_doctor_id;
    ELSE
        UPDATE employee
        SET deptment_id = emergency_dept_id,
            regist_level_id = normal_level_id,
            realname = '李静',
            role_type = 'DOCTOR',
            title_level = '主治医师',
            password_hash = '123456',
            delmark = TRUE
        WHERE id = emergency_doctor_id;
    END IF;

    SELECT id INTO imaging_tech_id FROM employee WHERE phone = '13910001003' ORDER BY id LIMIT 1;
    IF imaging_tech_id IS NULL THEN
        INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, email, delmark)
        VALUES (imaging_dept_id, '王影', 'MEDICAL_TECH', '主管技师', '123456', '13910001003', 'wang.imaging@example.local', TRUE)
        RETURNING id INTO imaging_tech_id;
    ELSE
        UPDATE employee
        SET deptment_id = imaging_dept_id,
            realname = '王影',
            role_type = 'MEDICAL_TECH',
            title_level = '主管技师',
            password_hash = '123456',
            delmark = TRUE
        WHERE id = imaging_tech_id;
    END IF;

    SELECT id INTO pharmacist_id FROM employee WHERE phone = '13910001004' ORDER BY id LIMIT 1;
    IF pharmacist_id IS NULL THEN
        INSERT INTO employee(deptment_id, realname, role_type, title_level, password_hash, phone, email, delmark)
        VALUES (pharmacy_dept_id, '陈药师', 'PHARMACIST', '主管药师', '123456', '13910001004', 'chen.pharmacy@example.local', TRUE)
        RETURNING id INTO pharmacist_id;
    ELSE
        UPDATE employee
        SET deptment_id = pharmacy_dept_id,
            realname = '陈药师',
            role_type = 'PHARMACIST',
            title_level = '主管药师',
            password_hash = '123456',
            delmark = TRUE
        WHERE id = pharmacist_id;
    END IF;

    FOR target_date IN SELECT CURRENT_DATE + i FROM generate_series(0, 6) AS s(i) LOOP
        IF NOT EXISTS (
            SELECT 1 FROM scheduling
            WHERE employee_id = neuro_doctor_id AND schedule_date = target_date AND noon = 'AM'
        ) THEN
            INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
            VALUES (neuro_doctor_id, neuro_dept_id, target_date, 'AM', 24, 'NORMAL', 'MANUAL');
        END IF;

        IF NOT EXISTS (
            SELECT 1 FROM scheduling
            WHERE employee_id = emergency_doctor_id AND schedule_date = target_date AND noon = 'PM'
        ) THEN
            INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type)
            VALUES (emergency_doctor_id, emergency_dept_id, target_date, 'PM', 32, 'NORMAL', 'MANUAL');
        END IF;
    END LOOP;

    IF NOT EXISTS (SELECT 1 FROM medical_technology WHERE tech_code = 'BIZ-CT-HEAD') THEN
        INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
        VALUES ('BIZ-CT-HEAD', '头颅CT平扫', '64排CT', 180.00, 'CHECK', '检查费', imaging_dept_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM medical_technology WHERE tech_code = 'BIZ-BLOOD-ROUTINE') THEN
        INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
        VALUES ('BIZ-BLOOD-ROUTINE', '血常规', '静脉血', 25.00, 'INSPECTION', '检验费', imaging_dept_id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM medical_technology WHERE tech_code = 'BIZ-WOUND-DRESSING') THEN
        INSERT INTO medical_technology(tech_code, tech_name, tech_format, tech_price, tech_type, price_type, deptment_id)
        VALUES ('BIZ-WOUND-DRESSING', '清创换药', '门诊处置', 35.00, 'DISPOSAL', '处置费', emergency_dept_id);
    END IF;

    INSERT INTO drug_info(drug_code, drug_name, drug_format, drug_unit, manufacturer, drug_dosage, drug_type, drug_price, stock_num, mnemonic_code)
    SELECT * FROM (VALUES
        ('BIZ-DRUG-MANNITOL', '甘露醇注射液', '250ml:50g', '瓶', '华北制药', '注射液', '西药', 12.50::NUMERIC, 120, 'GLCZSY'),
        ('BIZ-DRUG-ASPIRIN', '阿司匹林肠溶片', '100mg*30片', '盒', '拜耳医药', '片剂', '西药', 18.00::NUMERIC, 180, 'ASPLCRP'),
        ('BIZ-DRUG-MECOBALAMIN', '甲钴胺片', '0.5mg*20片', '盒', '卫材药业', '片剂', '西药', 28.00::NUMERIC, 95, 'JGAP'),
        ('BIZ-DRUG-OMEPRAZOLE', '奥美拉唑肠溶胶囊', '20mg*14粒', '盒', '常州制药', '胶囊', '西药', 22.80::NUMERIC, 88, 'AMLZCRJN'),
        ('BIZ-DRUG-CEFIKSIM', '头孢克肟片', '0.1g*12片', '盒', '广州白云山', '片剂', '抗菌药', 32.00::NUMERIC, 76, 'TBKWP'),
        ('BIZ-DRUG-AMLODIPINE', '苯磺酸氨氯地平片', '5mg*28片', '盒', '辉瑞制药', '片剂', '西药', 25.00::NUMERIC, 110, 'BHSALDPP')
    ) AS seed(drug_code, drug_name, drug_format, drug_unit, manufacturer, drug_dosage, drug_type, drug_price, stock_num, mnemonic_code)
    WHERE NOT EXISTS (
        SELECT 1 FROM drug_info d WHERE d.drug_code = seed.drug_code
    );

    FOR seeded_drug_id IN SELECT id FROM drug_info WHERE drug_code LIKE 'BIZ-DRUG-%' LOOP
        IF NOT EXISTS (SELECT 1 FROM drug_stock_record WHERE drug_stock_record.drug_id = seeded_drug_id AND record_type = 'IN') THEN
            INSERT INTO drug_stock_record(drug_id, record_type, quantity, before_stock, after_stock, operator_id, reason)
            SELECT seeded_drug_id, 'IN', stock_num, 0, stock_num, pharmacist_id, '业务演示基础库存初始化'
            FROM drug_info
            WHERE id = seeded_drug_id;
        END IF;
    END LOOP;
END $$;
