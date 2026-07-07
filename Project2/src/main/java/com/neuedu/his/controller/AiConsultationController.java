package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ClinicalAiStreamService;
import com.neuedu.his.service.ConsultationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

@RestController
@RequestMapping("/api/ai/consultation")
public class AiConsultationController {

    @Autowired
    private ConsultationService consultationService;

    @Autowired
    private ClinicalAiStreamService clinicalAiStreamService;

    @PostMapping("/triage")
    public ConsultationResponseVO triage(@RequestBody @Valid ConsultationRequestDTO request) {
        return consultationService.triage(request);
    }

    @PostMapping(value = "/triage/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public StreamingResponseBody triageStream(@RequestBody @Valid ConsultationRequestDTO request) {
        return outputStream -> clinicalAiStreamService.streamConsultation(request, outputStream);
    }
}
