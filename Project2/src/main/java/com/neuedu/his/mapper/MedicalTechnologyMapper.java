package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.MedicalTechnology;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface MedicalTechnologyMapper {

    @Select("SELECT * FROM medical_technology WHERE id = #{id}")
    MedicalTechnology selectById(Integer id);

    @Select("SELECT * FROM medical_technology WHERE tech_type = #{techType}")
    List<MedicalTechnology> selectByType(String techType);

    @Select("SELECT * FROM medical_technology WHERE deptment_id = #{deptId}")
    List<MedicalTechnology> selectByDept(Integer deptId);
}