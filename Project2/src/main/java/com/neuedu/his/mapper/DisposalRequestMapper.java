package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.DisposalRequest;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface DisposalRequestMapper {

    @Insert("INSERT INTO disposal_request(register_id, medical_technology_id, disposal_info, disposal_position, creation_time, disposal_state) " +
            "VALUES(#{registerId}, #{medicalTechnologyId}, #{disposalInfo}, #{disposalPosition}, NOW(), 'CREATED')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(DisposalRequest disposalRequest);

    @Select("SELECT * FROM disposal_request WHERE id = #{id}")
    DisposalRequest selectById(Integer id);

    List<DisposalRequest> selectByRegisterId(Integer registerId);

    int updateResult(@Param("id") Integer id,
                     @Param("disposalResult") String disposalResult,
                     @Param("disposalEmployeeId") Integer disposalEmployeeId);

    int updateState(@Param("id") Integer id, @Param("disposalState") String disposalState);
}