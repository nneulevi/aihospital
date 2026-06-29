package com.neuedu.his.mapper;

import com.neuedu.his.model.entity.AiGeneratedReport;
import org.apache.ibatis.annotations.Insert;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Options;
import org.apache.ibatis.annotations.Param;
import org.apache.ibatis.annotations.Select;
import org.apache.ibatis.annotations.Update;

import java.util.List;

@Mapper
public interface AiGeneratedReportMapper {

    @Insert("INSERT INTO ai_generated_report(request_id, register_id, report_type, ai_raw_content, ai_structured_data, " +
            "final_content, reference_source, ai_model_version, generation_time, status) " +
            "VALUES(#{requestId}, #{registerId}, #{reportType}, #{aiRawContent}, #{aiStructuredData}, " +
            "#{finalContent}, #{referenceSource}, #{aiModelVersion}, NOW(), 'DRAFT')")
    @Options(useGeneratedKeys = true, keyProperty = "id")
    int insert(AiGeneratedReport report);

    @Select("SELECT * FROM ai_generated_report WHERE id = #{id}")
    AiGeneratedReport selectById(Integer id);

    @Select("SELECT * FROM ai_generated_report WHERE request_id = #{requestId} AND report_type = #{reportType}")
    AiGeneratedReport selectByRequestId(@Param("requestId") Integer requestId, @Param("reportType") String reportType);

    @Select("SELECT * FROM ai_generated_report WHERE register_id = #{registerId} ORDER BY generation_time DESC")
    List<AiGeneratedReport> selectByRegisterId(Integer registerId);

    @Update("UPDATE ai_generated_report SET is_confirmed = 1, confirmed_by = #{confirmedBy}, " +
            "confirmed_time = NOW(), status = 'CONFIRMED', final_content = #{finalContent} WHERE id = #{id}")
    int confirmReport(@Param("id") Integer id, @Param("confirmedBy") Integer confirmedBy, @Param("finalContent") String finalContent);

    @Update("UPDATE ai_generated_report SET status = #{status} WHERE id = #{id}")
    int updateStatus(@Param("id") Integer id, @Param("status") String status);
}