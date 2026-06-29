package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ScheduleGenerateRequestDTO;
import com.neuedu.his.model.dto.ScheduleResultQueryDTO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleGenerateResponseVO;
import com.neuedu.his.model.vo.ScheduleResultVO;
import com.neuedu.his.service.ScheduleService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/ai/schedule")
public class AiScheduleController {

    @Autowired
    private ScheduleService scheduleService;

    @PostMapping("/generate")
    public ScheduleGenerateResponseVO generate(@RequestBody @Valid ScheduleGenerateRequestDTO request) {
        return scheduleService.generate(request);
    }

    @GetMapping("/result")
    public PageResult<ScheduleResultVO> getResults(@Valid ScheduleResultQueryDTO query) {
        return scheduleService.getResults(query);
    }
}