package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ConsultationService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/consultation")
public class AiConsultationController {

    @Autowired
    private ConsultationService consultationService;

    @PostMapping("/triage")
    public ConsultationResponseVO triage(@RequestBody @Valid ConsultationRequestDTO request) {
        return consultationService.triage(request);
    }
}