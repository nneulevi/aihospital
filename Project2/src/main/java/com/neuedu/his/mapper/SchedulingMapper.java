package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.Scheduling;
import com.neuedu.his.model.vo.ScheduleSourceVO;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.time.LocalDate;
import java.util.List;

@Mapper
public interface SchedulingMapper {

    @Insert("INSERT INTO scheduling(employee_id, deptment_id, schedule_date, noon, regist_quota, schedule_status, source_type) " +
            "VALUES(#{employeeId}, #{deptmentId}, #{scheduleDate}, #{noon}, #{registQuota}, #{scheduleStatus}, #{sourceType})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(Scheduling scheduling);

    @Select("SELECT * FROM scheduling WHERE id = #{id}")
    Scheduling selectById(Integer id);

    List<Scheduling> selectByCondition(Integer deptId, Integer employeeId, LocalDate startDate, LocalDate endDate);

    List<Scheduling> selectAvailableDoctors(Integer deptId, LocalDate scheduleDate, String noon);

    List<ScheduleSourceVO> selectSources(@Param("deptId") Integer deptId,
                                         @Param("doctorId") Integer doctorId,
                                         @Param("startDate") LocalDate startDate,
                                         @Param("endDate") LocalDate endDate);

    @Update("UPDATE scheduling SET regist_quota = #{registQuota}, update_time = NOW() WHERE id = #{id}")
    int updateQuota(@Param("id") Integer id, @Param("registQuota") Integer registQuota);

    @Update("UPDATE scheduling SET schedule_status = #{scheduleStatus}, update_time = NOW() WHERE id = #{id}")
    int updateStatus(@Param("id") Integer id, @Param("scheduleStatus") String scheduleStatus);
}
