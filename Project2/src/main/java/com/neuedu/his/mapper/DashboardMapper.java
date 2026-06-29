package com.neuedu.his.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.math.BigDecimal;

@Mapper
public interface DashboardMapper {

    @Select("SELECT COUNT(*) FROM register WHERE visit_date = CURRENT_DATE")
    Long countTodayRegistrations();

    @Select("SELECT COUNT(*) FROM register WHERE visit_state IN ('REGISTERED', 'DOCTOR_RECEIVED', 'ONGOING')")
    Long countActivePatients();

    @Select("""
            SELECT COALESCE((
                SELECT SUM(total_amount) FROM prescription WHERE prescription_status = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price)
                FROM check_request cr
                JOIN medical_technology mt ON cr.medical_technology_id = mt.id
                WHERE cr.check_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price)
                FROM inspection_request ir
                JOIN medical_technology mt ON ir.medical_technology_id = mt.id
                WHERE ir.inspection_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price)
                FROM disposal_request dr
                JOIN medical_technology mt ON dr.medical_technology_id = mt.id
                WHERE dr.disposal_state = 'CREATED'
            ), 0)
            """)
    BigDecimal sumPendingChargeAmount();

    @Select("SELECT COUNT(*) FROM drug_info WHERE COALESCE(stock_num, 0) < 10")
    Long countStockAlerts();

    @Select("SELECT COUNT(*) FROM ai_image_analysis WHERE DATE(analysis_time) = CURRENT_DATE")
    Long countTodayAiAnalyses();

    @Select("SELECT COUNT(*) FROM ai_generated_report WHERE COALESCE(is_confirmed, 0) = 0")
    Long countPendingReports();

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'REGISTERED'")
    Long countDoctorPending(@Param("doctorId") Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'DOCTOR_RECEIVED'")
    Long countDoctorConsulting(@Param("doctorId") Integer doctorId);

    @Select("""
            SELECT COUNT(*)
            FROM register
            WHERE employee_id = #{doctorId}
              AND visit_state IN ('DIAGNOSIS_DONE', 'FINISHED')
              AND visit_date = CURRENT_DATE
            """)
    Long countDoctorFinishedToday(@Param("doctorId") Integer doctorId);

    @Select("""
            SELECT COUNT(*)
            FROM check_request cr
            JOIN register r ON cr.register_id = r.id
            WHERE r.employee_id = #{doctorId}
              AND cr.check_state = 'CREATED'
            """)
    Long countDoctorPendingChecks(@Param("doctorId") Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE patient_id = #{patientId}")
    Long countPatientRecords(@Param("patientId") Integer patientId);

    @Select("""
            SELECT COALESCE((
                SELECT COUNT(*) FROM prescription p
                JOIN register r ON p.register_id = r.id
                WHERE r.patient_id = #{patientId} AND p.prescription_status = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT COUNT(*) FROM check_request cr
                JOIN register r ON cr.register_id = r.id
                WHERE r.patient_id = #{patientId} AND cr.check_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT COUNT(*) FROM inspection_request ir
                JOIN register r ON ir.register_id = r.id
                WHERE r.patient_id = #{patientId} AND ir.inspection_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT COUNT(*) FROM disposal_request dr
                JOIN register r ON dr.register_id = r.id
                WHERE r.patient_id = #{patientId} AND dr.disposal_state = 'CREATED'
            ), 0)
            """)
    Long countPatientUnpaidOrders(@Param("patientId") Integer patientId);

    @Select("""
            SELECT COALESCE((
                SELECT SUM(p.total_amount) FROM prescription p
                JOIN register r ON p.register_id = r.id
                WHERE r.patient_id = #{patientId} AND p.prescription_status = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price) FROM check_request cr
                JOIN register r ON cr.register_id = r.id
                JOIN medical_technology mt ON cr.medical_technology_id = mt.id
                WHERE r.patient_id = #{patientId} AND cr.check_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price) FROM inspection_request ir
                JOIN register r ON ir.register_id = r.id
                JOIN medical_technology mt ON ir.medical_technology_id = mt.id
                WHERE r.patient_id = #{patientId} AND ir.inspection_state = 'CREATED'
            ), 0)
            + COALESCE((
                SELECT SUM(mt.tech_price) FROM disposal_request dr
                JOIN register r ON dr.register_id = r.id
                JOIN medical_technology mt ON dr.medical_technology_id = mt.id
                WHERE r.patient_id = #{patientId} AND dr.disposal_state = 'CREATED'
            ), 0)
            """)
    BigDecimal sumPatientUnpaidAmount(@Param("patientId") Integer patientId);

    @Select("""
            SELECT visit_state
            FROM register
            WHERE patient_id = #{patientId}
            ORDER BY visit_date DESC, id DESC
            LIMIT 1
            """)
    String selectPatientLatestVisitState(@Param("patientId") Integer patientId);
}
