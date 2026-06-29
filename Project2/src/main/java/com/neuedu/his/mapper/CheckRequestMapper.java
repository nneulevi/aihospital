package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.CheckRequest;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface CheckRequestMapper {

    @Insert("INSERT INTO check_request(register_id, medical_technology_id, check_info, check_position, creation_time, check_state) " +
            "VALUES(#{registerId}, #{medicalTechnologyId}, #{checkInfo}, #{checkPosition}, NOW(), 'CREATED')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(CheckRequest checkRequest);

    @Select("SELECT * FROM check_request WHERE id = #{id}")
    CheckRequest selectById(Integer id);

    List<CheckRequest> selectByRegisterId(Integer registerId);

    int updateResult(@Param("id") Integer id,
                     @Param("checkResult") String checkResult,
                     @Param("checkEmployeeId") Integer checkEmployeeId,
                     @Param("checkRemark") String checkRemark);

    int updateState(@Param("id") Integer id, @Param("checkState") String checkState);

    int updateExecute(@Param("id") Integer id,
                      @Param("checkEmployeeId") Integer checkEmployeeId,
                      @Param("checkRemark") String checkRemark);
}
