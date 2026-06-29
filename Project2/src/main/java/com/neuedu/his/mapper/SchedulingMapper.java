package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Scheduling;
import com.neuedu.his.model.vo.DoctorListVO;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Update;
import org.apache.ibatis.annotations.Options;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface SchedulingMapper {

    // ==================== 原有方法 ====================

    @Select("SELECT * FROM scheduling WHERE id = #{id}")
    Scheduling selectById(@Param("id") Integer id);

    @Select("SELECT * FROM scheduling WHERE employee_id = #{doctorId} " +
            "AND schedule_date = #{visitDate} AND noon = #{noon} " +
            "AND schedule_status = 'ACTIVE'")
    Scheduling selectByDoctorAndDate(@Param("doctorId") Integer doctorId,
                                     @Param("visitDate") LocalDate visitDate,
                                     @Param("noon") String noon);

    @Insert("INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, " +
            "regist_quota, schedule_status, source_type, create_time, update_time) " +
            "VALUES(#{employeeId}, #{deptmentId}, #{scheduleDate}, #{noon}, " +
            "#{registQuota}, #{scheduleStatus}, #{sourceType}, NOW(), NOW())")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Scheduling scheduling);

    @Update("UPDATE scheduling SET employee_id = #{employeeId}, deptment_id = #{deptmentId}, " +
            "schedule_date = #{scheduleDate}, noon = #{noon}, regist_quota = #{registQuota}, " +
            "schedule_status = #{scheduleStatus}, source_type = #{sourceType}, update_time = NOW() " +
            "WHERE id = #{id}")
    int update(Scheduling scheduling);

    // ==================== 新增方法 ====================

    /**
     * 查询医生排班列表 - 使用 XML 配置
     */
    List<DoctorListVO> selectDoctorList(@Param("deptId") Integer deptId,
                                        @Param("visitDate") LocalDate visitDate,
                                        @Param("noon") String noon,
                                        @Param("offset") Integer offset,
                                        @Param("limit") Integer limit);

    /**
     * 统计医生排班总数 - 使用 XML 配置
     */
    Long countDoctorList(@Param("deptId") Integer deptId,
                         @Param("visitDate") LocalDate visitDate,
                         @Param("noon") String noon);
}