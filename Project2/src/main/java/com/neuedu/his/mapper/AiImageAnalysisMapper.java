package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiImageAnalysis;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface AiImageAnalysisMapper {

    @Insert("INSERT INTO ai_image_analysis(check_request_id, register_id, file_path, ai_findings, ai_annotation, ai_conclusion, confidence, analysis_time, ai_model_version) " +
            "VALUES(#{checkRequestId}, #{registerId}, #{filePath}, #{aiFindings}, #{aiAnnotation}, #{aiConclusion}, #{confidence}, NOW(), #{aiModelVersion})")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiImageAnalysis aiImageAnalysis);

    @Select("SELECT * FROM ai_image_analysis WHERE id = #{id}")
    AiImageAnalysis selectById(Integer id);

    @Select("SELECT * FROM ai_image_analysis WHERE check_request_id = #{checkRequestId}")
    AiImageAnalysis selectByCheckRequestId(Integer checkRequestId);

    @Update("UPDATE ai_image_analysis SET is_reviewed = 1, reviewed_by = #{reviewedBy}, reviewed_time = NOW() WHERE id = #{id}")
    int updateReview(Integer id, Integer reviewedBy);

    @Select("SELECT * FROM ai_image_analysis WHERE is_reviewed = 0 ORDER BY analysis_time DESC")
    List<AiImageAnalysis> selectUnreviewed();
}