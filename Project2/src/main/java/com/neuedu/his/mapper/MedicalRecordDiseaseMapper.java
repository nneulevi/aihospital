package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.MedicalRecordDisease;
import org.apache.ibatis.annotations.Delete;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface MedicalRecordDiseaseMapper {


    @Insert("INSERT INTO medical_record_disease(medical_record_id, disease_id) " +
            "VALUES(#{medicalRecordId}, #{diseaseId})")
    int insert(MedicalRecordDisease medicalRecordDisease);

    @Select("SELECT * FROM medical_record_disease WHERE medical_record_id = #{medicalRecordId}")
    List<MedicalRecordDisease> selectByMedicalRecordId(Integer medicalRecordId);

    @Delete("DELETE FROM medical_record_disease WHERE medical_record_id = #{medicalRecordId}")
    int deleteByMedicalRecordId(Integer medicalRecordId);


    // 建议删除这个方法，或者用其他方式查询
    @Select("SELECT * FROM medical_record_disease WHERE medical_record_id = #{medicalRecordId} AND disease_id = #{diseaseId}")
    MedicalRecordDisease selectByCompositeId(@Param("medicalRecordId") Integer medicalRecordId,
                                             @Param("diseaseId") Integer diseaseId);
}