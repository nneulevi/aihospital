package com.neuedu.his.controller;

import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.ClinicalAiStreamService;
import com.neuedu.his.service.DiagnosisService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

@RestController
@RequestMapping("/api/ai/diagnosis")
public class AiDiagnosisController {

    @Autowired
    private DiagnosisService diagnosisService;

    @Autowired
    private ClinicalAiStreamService clinicalAiStreamService;

    @PostMapping("/suggest")
    public DiagnosisSuggestResponseVO suggest(@RequestBody @Valid DiagnosisSuggestRequestDTO request) {
        return diagnosisService.suggest(request);
    }

    @PostMapping(value = "/suggest/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public StreamingResponseBody suggestStream(@RequestBody @Valid DiagnosisSuggestRequestDTO request) {
        return outputStream -> clinicalAiStreamService.streamDiagnosis(request, outputStream);
    }
}
