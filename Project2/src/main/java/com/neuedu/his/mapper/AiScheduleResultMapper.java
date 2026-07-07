package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiScheduleResult;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface AiScheduleResultMapper {

    @Insert("INSERT INTO ai_schedule_result(employee_id, deptment_id, schedule_date, shift_type, regist_quota, is_generated, is_modified, source_type) " +
            "VALUES(#{employeeId}, #{deptmentId}, #{scheduleDate}, #{shiftType}, #{registQuota}, #{isGenerated}, #{isModified}, #{sourceType})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiScheduleResult aiScheduleResult);

    int batchInsert(@Param("results") List<AiScheduleResult> results);

    @Select("SELECT * FROM ai_schedule_result WHERE id = #{id}")
    AiScheduleResult selectById(Integer id);

    @Select("""
            SELECT r.*
            FROM ai_schedule_result r
                     JOIN employee e ON r.employee_id = e.id
            WHERE r.deptment_id = #{deptId}
              AND r.schedule_date BETWEEN #{startDate} AND #{endDate}
              AND e.delmark = TRUE
              AND e.realname NOT LIKE '%E2E%'
              AND e.realname NOT LIKE '%User Logic%'
              AND e.realname NOT LIKE '%Extended%'
              AND e.realname NOT LIKE '%项目验收%'
              AND e.realname NOT LIKE '%验收%'
              AND e.realname NOT LIKE '%测试%'
            ORDER BY r.schedule_date, r.shift_type
            """)
    List<AiScheduleResult> selectByDateRange(@Param("deptId") Integer deptId,
                                              @Param("startDate") LocalDate startDate,
                                              @Param("endDate") LocalDate endDate);

    @Select("SELECT * FROM ai_schedule_result WHERE employee_id = #{employeeId} AND schedule_date = #{scheduleDate}")
    AiScheduleResult selectByEmployeeAndDate(@Param("employeeId") Integer employeeId, @Param("scheduleDate") LocalDate scheduleDate);
}
