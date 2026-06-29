package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ReportGenerateRequestDTO;
import com.neuedu.his.model.vo.ReportGenerateResponseVO;
import com.neuedu.his.service.ReportService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/report")
public class AiReportController {

    @Autowired
    private ReportService reportService;

    @PostMapping("/generate")
    public ReportGenerateResponseVO generate(@RequestBody @Valid ReportGenerateRequestDTO request) {
        return reportService.generate(request);
    }
}