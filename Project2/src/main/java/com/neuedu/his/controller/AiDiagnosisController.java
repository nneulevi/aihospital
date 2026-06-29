package com.neuedu.his.controller;

import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.DiagnosisService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/diagnosis")
public class AiDiagnosisController {

    @Autowired
    private DiagnosisService diagnosisService;

    @PostMapping("/suggest")
    public DiagnosisSuggestResponseVO suggest(@RequestBody @Valid DiagnosisSuggestRequestDTO request) {
        return diagnosisService.suggest(request);
    }
}