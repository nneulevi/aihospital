package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Register;
import com.neuedu.his.model.vo.*;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;
import org.apache.ibatis.annotations.Options;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

@Mapper
public interface RegisterMapper {

    // ==================== 原有方法 ====================

    @Select("SELECT * FROM register WHERE id = #{id}")
    Register selectById(@Param("id") Integer id);

    @Insert("INSERT INTO register(visit_no, patient_id, visit_date, noon, deptment_id, employee_id, " +
            "regist_level_id, settle_category_id, source_type, queue_no, regist_method, regist_money, " +
            "visit_state, checkin_status, checkin_time, create_time, update_time) " +
            "VALUES(#{visitNo}, #{patientId}, #{visitDate}, #{noon}, #{deptmentId}, #{employeeId}, " +
            "#{registLevelId}, #{settleCategoryId}, #{sourceType}, #{queueNo}, #{registMethod}, " +
            "#{registMoney}, #{visitState}, #{checkinStatus}, #{checkinTime}, NOW(), NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Register register);

    @Update("UPDATE register SET visit_no = #{visitNo}, patient_id = #{patientId}, " +
            "visit_date = #{visitDate}, noon = #{noon}, deptment_id = #{deptmentId}, " +
            "employee_id = #{employeeId}, regist_level_id = #{registLevelId}, " +
            "settle_category_id = #{settleCategoryId}, source_type = #{sourceType}, " +
            "queue_no = #{queueNo}, regist_method = #{registMethod}, regist_money = #{registMoney}, " +
            "visit_state = #{visitState}, checkin_status = #{checkinStatus}, " +
            "checkin_time = #{checkinTime}, update_time = NOW() WHERE id = #{id}")
    int update(Register register);

    // ==================== 新增方法 ====================

    /**
     * 统计指定医生某天某午别的已挂号人数
     */
    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} " +
            "AND visit_date::date = #{visitDate} AND noon = #{noon} " +
            "AND visit_state != 'CANCELLED'")
    Integer countByScheduling(@Param("doctorId") Integer doctorId,
                              @Param("visitDate") LocalDate visitDate,
                              @Param("noon") String noon);

    /**
     * 查询患者挂号记录（分页）- 使用 XML 配置
     */
    List<PatientRecordListVO> selectPatientRecords(@Param("patientId") Integer patientId,
                                                   @Param("visitState") String visitState,
                                                   @Param("offset") Integer offset,
                                                   @Param("limit") Integer limit);

    /**
     * 统计患者挂号记录总数 - 使用 XML 配置
     */
    Long countPatientRecords(@Param("patientId") Integer patientId,
                             @Param("visitState") String visitState);

    /**
     * 查询挂号详情（含患者信息、诊断等）- 使用 XML 配置
     */
    PatientRecordListVO selectPatientRecordDetail(@Param("registerId") Integer registerId);

    /**
     * 查询今日可报到列表 - 使用 XML 配置
     */
    List<TodayRegisterVO> selectTodayRegisters(@Param("patientId") Integer patientId,
                                               @Param("today") LocalDate today);

    /**
     * 查询候诊队列 - 使用 XML 配置
     */
    List<QueueItemVO> selectQueueList(@Param("doctorId") Integer doctorId,
                                      @Param("visitDate") LocalDateTime visitDate,
                                      @Param("noon") String noon);

    /**
     * 计算前面还有多少人
     */
    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} " +
            "AND visit_date::date = #{visitDate}::date AND noon = #{noon} " +
            "AND checkin_status = 1 AND queue_no < #{currentQueueNo} " +
            "AND visit_state != 'CANCELLED'")
    Integer countAhead(@Param("doctorId") Integer doctorId,
                       @Param("visitDate") LocalDateTime visitDate,
                       @Param("noon") String noon,
                       @Param("currentQueueNo") Integer currentQueueNo);

    /**
     * 获取当前叫号（已报到的最小排队号）
     */
    @Select("SELECT MIN(queue_no) FROM register WHERE employee_id = #{doctorId} " +
            "AND visit_date::date = #{visitDate}::date AND noon = #{noon} " +
            "AND checkin_status = 1 AND visit_state = 'CONSULTING'")
    Integer getCurrentCalling(@Param("doctorId") Integer doctorId,
                              @Param("visitDate") LocalDateTime visitDate,
                              @Param("noon") String noon);

    /**
     * 获取有候诊队列的科室列表
     */
    @Select("SELECT DISTINCT d.id AS deptId, d.dept_name AS deptName " +
            "FROM register r LEFT JOIN department d ON r.deptment_id = d.id " +
            "WHERE r.patient_id = #{patientId} " +
            "AND r.visit_state IN ('REGISTERED', 'CONSULTING') AND r.checkin_status = 1 " +
            "AND r.visit_date >= NOW() - INTERVAL '1 DAY'")
    List<DeptQueueVO> selectQueueDepts(@Param("patientId") Integer patientId);

    /**
     * 统计今日候诊人数（用于角标）
     */
    @Select("SELECT COUNT(*) FROM register WHERE patient_id = #{patientId} " +
            "AND visit_date::date = #{today} AND visit_state = 'REGISTERED' AND checkin_status = 0")
    Integer countTodayQueue(@Param("patientId") Integer patientId,
                            @Param("today") LocalDate today);

    /**
     * 查询挂号费订单 - 使用 XML 配置
     */
    List<OrderListVO> selectRegisterOrders(@Param("patientId") Integer patientId,
                                           @Param("orderState") String orderState,
                                           @Param("offset") Integer offset,
                                           @Param("limit") Integer limit);

    /**
     * 查询就诊详情（医生端用）- 使用 XML 配置
     */
    Register selectVisitDetail(@Param("registerId") Integer registerId);

    // ==================== 医生端 ====================

    /**
     * 查询医生的患者列表（待诊/就诊中/已完成）- 使用 XML 配置
     */
    List<Register> selectDoctorPatients(@Param("doctorId") Integer doctorId,
                                        @Param("visitState") String visitState);

    // ==================== 医生统计 ====================

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_date = CURRENT_DATE AND visit_state = 'FINISHED'")
    int countTodayVisitsByDoctorId(Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_date >= DATE_TRUNC('month', CURRENT_DATE) AND visit_state = 'FINISHED'")
    int countMonthVisitsByDoctorId(Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'FINISHED'")
    int countTotalVisitsByDoctorId(Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'REGISTERED'")
    int countPendingByDoctorId(Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'CONSULTING'")
    int countConsultingByDoctorId(Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_state = 'FINISHED'")
    int countFinishedByDoctorId(Integer doctorId);

    @Update("UPDATE register SET visit_state = #{visitState} WHERE id = #{id}")
    int updateState(@Param("id") Integer id, @Param("visitState") String visitState);

    @Select("SELECT COUNT(DISTINCT r.patient_id) FROM register r " +
            "WHERE r.employee_id = #{doctorId} AND r.visit_state = 'FINISHED' " +
            "AND r.patient_id IN (SELECT patient_id FROM register WHERE visit_state = 'FINISHED' GROUP BY patient_id HAVING COUNT(*) >= 2)")
    int countRevisitPatientsByDoctorId(@Param("doctorId") Integer doctorId);

    // ==================== 管理员端 - 部门统计 ====================

    @Select("SELECT COUNT(*) FROM register WHERE deptment_id = #{deptId} AND visit_state = 'FINISHED'")
    int countFinishedByDeptId(@Param("deptId") Integer deptId);

    @Select("SELECT COUNT(DISTINCT patient_id) FROM register WHERE deptment_id = #{deptId} AND visit_state = 'FINISHED'")
    int countPatientsByDeptId(@Param("deptId") Integer deptId);

    @Select("SELECT DISTINCT patient_id FROM register WHERE deptment_id = #{deptId} AND visit_state = 'FINISHED' GROUP BY patient_id HAVING COUNT(*) >= 2")
    List<Integer> findRevisitPatientIdsByDeptId(@Param("deptId") Integer deptId);

}