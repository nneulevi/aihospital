package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiDiagnosisSuggestion;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface AiDiagnosisSuggestionMapper {

    @Insert("INSERT INTO ai_diagnosis_suggestion(medical_record_id, register_id, ai_diagnosis, disease_id, confidence, evidence_basis, suggestion_time, ai_model_version) " +
            "VALUES(#{medicalRecordId}, #{registerId}, #{aiDiagnosis}, #{diseaseId}, #{confidence}, #{evidenceBasis}, NOW(), #{aiModelVersion})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiDiagnosisSuggestion aiDiagnosisSuggestion);

    @Select("SELECT * FROM ai_diagnosis_suggestion WHERE id = #{id}")
    AiDiagnosisSuggestion selectById(Integer id);

    @Select("SELECT * FROM ai_diagnosis_suggestion WHERE medical_record_id = #{medicalRecordId}")
    List<AiDiagnosisSuggestion> selectByMedicalRecordId(Integer medicalRecordId);

    @Update("UPDATE ai_diagnosis_suggestion SET is_adopted = #{isAdopted}, doctor_feedback = #{doctorFeedback} WHERE id = #{id}")
    int updateFeedback(Integer id, Integer isAdopted, String doctorFeedback);
}