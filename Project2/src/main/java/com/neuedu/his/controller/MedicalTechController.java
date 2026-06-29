package com.neuedu.his.controller;

import com.neuedu.his.model.dto.MedicalTechExecuteRequestDTO;
import com.neuedu.his.model.dto.MedicalTechReportRequestDTO;
import com.neuedu.his.model.dto.MedicalTechTaskQueryDTO;
import com.neuedu.his.model.vo.MedicalTechInterpretationVO;
import com.neuedu.his.model.vo.MedicalTechTaskVO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.service.MedicalTechService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/medical-tech")
public class MedicalTechController {

    @Autowired
    private MedicalTechService medicalTechService;

    @GetMapping("/tasks")
    public PageResult<MedicalTechTaskVO> getTasks(@Valid MedicalTechTaskQueryDTO query) {
        return medicalTechService.getTasks(query);
    }

    @PostMapping("/tasks/{itemType}/{itemId}/execute")
    public void execute(@PathVariable String itemType,
                        @PathVariable Integer itemId,
                        @RequestBody @Valid MedicalTechExecuteRequestDTO request) {
        medicalTechService.execute(itemType, itemId, request);
    }

    @PostMapping("/tasks/{itemType}/{itemId}/report")
    public void report(@PathVariable String itemType,
                       @PathVariable Integer itemId,
                       @RequestBody @Valid MedicalTechReportRequestDTO request) {
        medicalTechService.report(itemType, itemId, request);
    }

    @PostMapping("/tasks/{itemType}/{itemId}/ai-interpret")
    public MedicalTechInterpretationVO aiInterpret(@PathVariable String itemType,
                                                   @PathVariable Integer itemId) {
        return medicalTechService.aiInterpret(itemType, itemId);
    }
}
