package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiConsultation;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;

import java.util.List;

@Mapper
public interface AiConsultationMapper {

    @Insert("INSERT INTO ai_consultation(patient_id, register_id, symptoms_desc, ai_recommend_dept, ai_diagnosis_hint, consultation_time, ai_model_version, status) " +
            "VALUES(#{patientId}, #{registerId}, #{symptomsDesc}, #{aiRecommendDept}, #{aiDiagnosisHint}, NOW(), #{aiModelVersion}, 1)")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiConsultation aiConsultation);

    @Select("SELECT * FROM ai_consultation WHERE id = #{id}")
    AiConsultation selectById(Integer id);

    @Select("SELECT * FROM ai_consultation WHERE patient_id = #{patientId} ORDER BY consultation_time DESC")
    List<AiConsultation> selectByPatientId(Integer patientId);

    @Select("SELECT * FROM ai_consultation WHERE register_id = #{registerId}")
    AiConsultation selectByRegisterId(Integer registerId);
}