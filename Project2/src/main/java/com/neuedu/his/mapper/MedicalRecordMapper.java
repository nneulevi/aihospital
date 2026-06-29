package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.MedicalRecord;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

@Mapper
public interface MedicalRecordMapper {

    @Insert("INSERT INTO medical_record(register_id, doctor_id, readme, present, present_treat, history, " +
            "allergy, physique, proposal, careful, diagnosis, cure, record_status) " +
            "VALUES(#{registerId}, #{doctorId}, #{readme}, #{present}, #{presentTreat}, #{history}, " +
            "#{allergy}, #{physique}, #{proposal}, #{careful}, #{diagnosis}, #{cure}, #{recordStatus})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(MedicalRecord medicalRecord);

    @Select("SELECT * FROM medical_record WHERE id = #{id}")
    MedicalRecord selectById(Integer id);

    @Select("SELECT * FROM medical_record WHERE register_id = #{registerId}")
    MedicalRecord selectByRegisterId(Integer registerId);

    int updateById(MedicalRecord medicalRecord);

    int updateStatus(@Param("id") Integer id, @Param("recordStatus") String recordStatus);
}