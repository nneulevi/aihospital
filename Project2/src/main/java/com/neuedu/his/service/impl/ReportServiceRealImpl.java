package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.AiGeneratedReportMapper;
import com.neuedu.his.mapper.AiImageAnalysisMapper;
import com.neuedu.his.mapper.CheckRequestMapper;
import com.neuedu.his.mapper.RegisterMapper;
import com.neuedu.his.model.dto.ReportGenerateRequestDTO;
import com.neuedu.his.model.entity.AiGeneratedReport;
import com.neuedu.his.model.entity.AiImageAnalysis;
import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.entity.Register;
import com.neuedu.his.model.vo.ReportGenerateResponseVO;
import com.neuedu.his.service.HeadCtAiWorkflowService;
import com.neuedu.his.service.ReportService;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.StringUtils;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

public class ReportServiceRealImpl implements ReportService {

    @Autowired
    private AiGeneratedReportMapper aiGeneratedReportMapper;

    @Autowired
    private AiImageAnalysisMapper aiImageAnalysisMapper;

    @Autowired
    private CheckRequestMapper checkRequestMapper;

    @Autowired
    private RegisterMapper registerMapper;

    @Autowired
    private HeadCtAiWorkflowService headCtAiWorkflowService;

    @Override
    public ReportGenerateResponseVO generate(ReportGenerateRequestDTO request) {
        CheckRequest checkRequest = checkRequestMapper.selectById(request.getCheckRequestId());
        if (checkRequest == null) {
            throw new BusinessException("检查申请不存在: " + request.getCheckRequestId());
        }

        AiImageAnalysis analysis = aiImageAnalysisMapper.selectByCheckRequestId(request.getCheckRequestId());
        if (analysis == null || !StringUtils.hasText(analysis.getAiAnnotation())) {
            throw new BusinessException("请先完成该检查申请的AI影像分析");
        }

        Map<String, Object> analysisSnapshot = JsonUtil.fromJson(analysis.getAiAnnotation(), Map.class);
        String taskId = Objects.toString(analysisSnapshot.get("task_id"), null);
        if (!StringUtils.hasText(taskId)) {
            throw new BusinessException("AI分析结果中缺少orchestrator task_id");
        }

        Register register = registerMapper.selectById(checkRequest.getRegisterId());
        Map<String, Object> reportResponse = headCtAiWorkflowService.createReportDraft(
                taskId, checkRequest, register, request.getReportType()
        );
        Map<String, Object> reportSnapshot = extractReportSnapshot(reportResponse);
        String content = extractReportContent(reportSnapshot);

        AiGeneratedReport report = new AiGeneratedReport();
        report.setRequestId(request.getCheckRequestId());
        report.setRegisterId(checkRequest.getRegisterId());
        report.setReportType(request.getReportType());
        report.setAiRawContent(content);
        report.setAiStructuredData(JsonUtil.toJson(reportSnapshot));
        report.setFinalContent(content);
        report.setReferenceSource("HeadCTReportService");
        report.setAiModelVersion(firstText(reportSnapshot.get("model_version"), reportSnapshot.get("ai_model_version"), "HeadCTReportService"));
        aiGeneratedReportMapper.insert(report);

        ReportGenerateResponseVO response = new ReportGenerateResponseVO();
        response.setReportId(report.getId());
        response.setReportContent(content);
        response.setStatus(firstText(reportSnapshot.get("status"), "DRAFT"));
        return response;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> extractReportSnapshot(Map<String, Object> response) {
        Object report = response.get("report");
        if (report instanceof Map<?, ?> reportMap) {
            return (Map<String, Object>) reportMap;
        }
        return response;
    }

    private String extractReportContent(Map<String, Object> report) {
        String content = firstText(
                report.get("report_content"),
                report.get("content"),
                report.get("final_content"),
                report.get("ai_raw_content")
        );
        if (StringUtils.hasText(content)) {
            return content;
        }

        Map<String, Object> sections = asMap(report.get("sections"));
        String findings = firstText(report.get("findings"), sections.get("findings"), "未返回明确检查所见");
        String impression = firstText(report.get("impression"), sections.get("impression"), "请医生审核后完善诊断意见");
        String recommendation = firstText(report.get("recommendation"), report.get("recommendations"), sections.get("recommendations"), "");

        StringBuilder builder = new StringBuilder();
        builder.append("【AI辅助检查报告】\n");
        builder.append("检查所见：").append(findings).append("\n");
        builder.append("诊断意见：").append(impression);
        if (StringUtils.hasText(recommendation)) {
            builder.append("\n建议：").append(recommendation);
        }
        return builder.toString();
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return new LinkedHashMap<>();
    }

    private String firstText(Object... values) {
        for (Object value : values) {
            String text = Objects.toString(value, null);
            if (StringUtils.hasText(text)) {
                return text;
            }
        }
        return "";
    }
}
