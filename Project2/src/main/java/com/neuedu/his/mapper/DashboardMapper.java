package com.neuedu.his.mapper;

import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.math.BigDecimal;
import java.util.List;
import com.neuedu.his.model.vo.DepartmentStatsVO;
import com.neuedu.his.model.vo.DoctorStatsVO;

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

    @Select("""
            SELECT e.id AS doctor_id,
                   e.realname AS doctor_name,
                   d.dept_name AS dept_name,
                   e.title_level AS title_level,
                   COALESCE(COUNT(CASE WHEN r.visit_date = CURRENT_DATE THEN 1 END), 0) AS today_registrations,
                   COALESCE(COUNT(CASE WHEN r.visit_state IN ('REGISTERED', 'DOCTOR_RECEIVED', 'ONGOING') THEN 1 END), 0) AS active_patients,
                   COALESCE(COUNT(CASE WHEN r.visit_state IN ('DIAGNOSIS_DONE', 'FINISHED') AND r.visit_date = CURRENT_DATE THEN 1 END), 0) AS finished_today,
                   COALESCE(COUNT(DISTINCT CASE WHEN cr.check_state = 'CREATED' THEN cr.id END), 0) AS pending_checks
            FROM employee e
            LEFT JOIN department d ON e.deptment_id = d.id
            LEFT JOIN register r ON r.employee_id = e.id
            LEFT JOIN check_request cr ON cr.register_id = r.id
            WHERE e.delmark = TRUE
              AND e.role_type = 'DOCTOR'
            GROUP BY e.id, e.realname, d.dept_name, e.title_level
            ORDER BY active_patients DESC, today_registrations DESC, e.id ASC
            """)
    List<DoctorStatsVO> selectDoctorStats();

    @Select("""
            SELECT d.id AS dept_id,
                   d.dept_name AS dept_name,
                   d.dept_type AS dept_type,
                   COALESCE(COUNT(DISTINCT CASE WHEN e.role_type = 'DOCTOR' AND e.delmark = TRUE THEN e.id END), 0) AS doctor_count,
                   COALESCE(COUNT(DISTINCT CASE WHEN r.visit_date = CURRENT_DATE THEN r.id END), 0) AS today_registrations,
                   COALESCE(COUNT(DISTINCT CASE WHEN r.visit_state IN ('REGISTERED', 'DOCTOR_RECEIVED', 'ONGOING') THEN r.id END), 0) AS active_patients,
                   COALESCE(SUM(CASE WHEN s.schedule_date = CURRENT_DATE AND s.schedule_status = 'NORMAL' THEN s.regist_quota ELSE 0 END), 0) AS schedule_quota,
                   COALESCE(COUNT(DISTINCT CASE WHEN cr.check_state = 'CREATED' THEN cr.id END), 0) AS pending_checks
            FROM department d
            LEFT JOIN employee e ON e.deptment_id = d.id
            LEFT JOIN register r ON r.deptment_id = d.id
            LEFT JOIN scheduling s ON s.deptment_id = d.id
            LEFT JOIN check_request cr ON cr.register_id = r.id
            WHERE d.delmark = TRUE
            GROUP BY d.id, d.dept_name, d.dept_type
            ORDER BY today_registrations DESC, active_patients DESC, d.id ASC
            """)
    List<DepartmentStatsVO> selectDepartmentStats();

    @Select("""
            SELECT COUNT(*)
            FROM register
            WHERE employee_id = #{doctorId}
              AND visit_date = CURRENT_DATE
              AND visit_state IN ('REGISTERED', 'CHECKED_IN')
            """)
    Long countDoctorPending(@Param("doctorId") Integer doctorId);

    @Select("""
            SELECT COUNT(*)
            FROM register
            WHERE employee_id = #{doctorId}
              AND visit_date = CURRENT_DATE
              AND visit_state = 'DOCTOR_RECEIVED'
            """)
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
            ORDER BY CASE
                         WHEN visit_state IN ('REFUNDED', 'CANCELLED') THEN 3
                         WHEN visit_date = CURRENT_DATE THEN 0
                         WHEN visit_date > CURRENT_DATE THEN 1
                         ELSE 2
                     END ASC,
                     CASE
                         WHEN visit_date > CURRENT_DATE AND visit_state NOT IN ('REFUNDED', 'CANCELLED') THEN visit_date
                     END ASC NULLS LAST,
                     visit_date DESC,
                     id DESC
            LIMIT 1
            """)
    String selectPatientLatestVisitState(@Param("patientId") Integer patientId);
}
