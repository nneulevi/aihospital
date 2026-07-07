package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Register;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface RegisterMapper {

    @Insert("INSERT INTO register(visit_no, patient_id, visit_date, noon, deptment_id, employee_id, " +
            "regist_level_id, settle_category_id, source_type, queue_no, regist_method, regist_money, visit_state) " +
            "VALUES(#{visitNo}, #{patientId}, #{visitDate}, #{noon}, #{deptmentId}, #{employeeId}, " +
            "#{registLevelId}, #{settleCategoryId}, #{sourceType}, #{queueNo}, #{registMethod}, #{registMoney}, #{visitState})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Register register);

    @Select("SELECT * FROM register WHERE id = #{id}")
    Register selectById(Integer id);

    @Update("UPDATE register SET visit_state = #{visitState} WHERE id = #{id}")
    int updateState(@Param("id") Integer id, @Param("visitState") String visitState);

    @Select("SELECT * FROM register WHERE id = #{id} AND visit_state IN ('REGISTERED', 'DOCTOR_RECEIVED')")
    Register selectCancelableById(Integer id);

    @Select("SELECT * FROM register WHERE id = #{id} AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED')")
    Register selectCancelableOrWaitingById(Integer id);

    @Select("SELECT COUNT(*) FROM register " +
            "WHERE deptment_id = #{deptId} " +
            "AND employee_id = #{doctorId} " +
            "AND visit_date = #{visitDate} " +
            "AND (noon = #{noon} OR (#{noon} = 'AM' AND noon = 'MORNING') OR (#{noon} = 'PM' AND noon = 'AFTERNOON')) " +
            "AND COALESCE(visit_state, '') NOT IN ('REFUNDED', 'CANCELLED')")
    int countActiveBySchedule(@Param("deptId") Integer deptId,
                              @Param("doctorId") Integer doctorId,
                              @Param("visitDate") LocalDate visitDate,
                              @Param("noon") String noon);

    @Select("SELECT COUNT(*) FROM register " +
            "WHERE patient_id = #{patientId} " +
            "AND deptment_id = #{deptId} " +
            "AND employee_id = #{doctorId} " +
            "AND visit_date = #{visitDate} " +
            "AND (noon = #{noon} OR (#{noon} = 'AM' AND noon = 'MORNING') OR (#{noon} = 'PM' AND noon = 'AFTERNOON')) " +
            "AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED', 'ONGOING', 'CONSULTING')")
    int countActiveByPatientSchedule(@Param("patientId") Integer patientId,
                                     @Param("deptId") Integer deptId,
                                     @Param("doctorId") Integer doctorId,
                                     @Param("visitDate") LocalDate visitDate,
                                     @Param("noon") String noon);

    @Select("SELECT COUNT(*) FROM register " +
            "WHERE patient_id = #{patientId} " +
            "AND employee_id = #{doctorId} " +
            "AND visit_date = #{visitDate} " +
            "AND visit_state IN ('REGISTERED', 'CHECKED_IN', 'DOCTOR_RECEIVED', 'ONGOING', 'CONSULTING')")
    int countActiveByPatientDoctorDate(@Param("patientId") Integer patientId,
                                       @Param("doctorId") Integer doctorId,
                                       @Param("visitDate") LocalDate visitDate);

    List<Register> selectPatientRecords(@Param("patientId") Integer patientId,
                                        @Param("startDate") LocalDate startDate,
                                        @Param("endDate") LocalDate endDate,
                                        @Param("visitState") String visitState);

    Register selectLatestTodayByPatient(@Param("patientId") Integer patientId,
                                        @Param("visitDate") LocalDate visitDate);

    int countWaitingAhead(@Param("deptId") Integer deptId,
                          @Param("doctorId") Integer doctorId,
                          @Param("visitDate") LocalDate visitDate,
                          @Param("noon") String noon,
                          @Param("queueNo") Integer queueNo);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId} AND visit_date = CURRENT_DATE")
    Long countDoctorTodayVisits(@Param("doctorId") Integer doctorId);

    @Select("""
            SELECT COUNT(*) FROM register
            WHERE employee_id = #{doctorId}
              AND visit_date >= date_trunc('month', CURRENT_DATE)::date
            """)
    Long countDoctorMonthVisits(@Param("doctorId") Integer doctorId);

    @Select("SELECT COUNT(*) FROM register WHERE employee_id = #{doctorId}")
    Long countDoctorTotalVisits(@Param("doctorId") Integer doctorId);

    List<Register> selectDoctorPatients(@Param("doctorId") Integer doctorId,
                                        @Param("visitState") String visitState,
                                        @Param("visitDate") LocalDate visitDate,
                                        @Param("noon") String noon);

    Register selectVisitDetail(Integer registerId);

    List<Register> selectChargeItems(Integer registerId);

    int cancelRegister(@Param("id") Integer id, @Param("cancelReason") String cancelReason);
}
