package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.InspectionRequest;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface InspectionRequestMapper {

    @Insert("INSERT INTO inspection_request(register_id, medical_technology_id, inspection_info, inspection_position, creation_time, inspection_state) " +
            "VALUES(#{registerId}, #{medicalTechnologyId}, #{inspectionInfo}, #{inspectionPosition}, NOW(), 'CREATED')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(InspectionRequest inspectionRequest);

    @Select("SELECT * FROM inspection_request WHERE id = #{id}")
    InspectionRequest selectById(Integer id);

    List<InspectionRequest> selectByRegisterId(Integer registerId);

    int updateResult(@Param("id") Integer id,
                     @Param("inspectionResult") String inspectionResult,
                     @Param("inspectionEmployeeId") Integer inspectionEmployeeId,
                     @Param("inspectionRemark") String inspectionRemark);

    int updateState(@Param("id") Integer id, @Param("inspectionState") String inspectionState);

    int updateExecute(@Param("id") Integer id,
                      @Param("inspectionEmployeeId") Integer inspectionEmployeeId,
                      @Param("inspectionRemark") String inspectionRemark);
}
