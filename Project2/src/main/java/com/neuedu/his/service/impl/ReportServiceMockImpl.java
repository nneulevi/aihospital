package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiGeneratedReportMapper;
import com.neuedu.his.mapper.CheckRequestMapper;
import com.neuedu.his.model.dto.ReportGenerateRequestDTO;
import com.neuedu.his.model.entity.AiGeneratedReport;
import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.vo.ReportGenerateResponseVO;
import com.neuedu.his.service.ReportService;
import org.springframework.beans.factory.annotation.Autowired;

public class ReportServiceMockImpl implements ReportService {

    @Autowired
    private AiGeneratedReportMapper aiGeneratedReportMapper;

    @Autowired
    private CheckRequestMapper checkRequestMapper;

    @Override
    public ReportGenerateResponseVO generate(ReportGenerateRequestDTO request) {
        CheckRequest checkRequest = checkRequestMapper.selectById(request.getCheckRequestId());

        String rawContent = "【AI影像报告】\n" +
                "检查项目：" + request.getReportType() + "\n" +
                "检查所见：未见明显异常征象。\n" +
                "诊断意见：建议结合临床，必要时复查。";

        AiGeneratedReport report = new AiGeneratedReport();
        report.setRequestId(request.getCheckRequestId());
        report.setRegisterId(checkRequest != null ? checkRequest.getRegisterId() : 0);
        report.setReportType(request.getReportType());
        report.setAiRawContent(rawContent);
        report.setAiStructuredData("{\"findings\":\"未见明显异常\",\"conclusion\":\"正常\",\"confidence\":0.95}");
        report.setFinalContent(rawContent);
        report.setReferenceSource("Mock知识库-v1.0");
        report.setAiModelVersion("Mock-v1.0");
        aiGeneratedReportMapper.insert(report);

        ReportGenerateResponseVO response = new ReportGenerateResponseVO();
        response.setReportId(report.getId());
        response.setReportContent(rawContent);
        response.setStatus("DRAFT");
        return response;
    }
}
