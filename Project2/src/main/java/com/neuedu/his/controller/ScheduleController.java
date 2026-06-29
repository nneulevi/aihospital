package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ScheduleQuotaUpdateDTO;
import com.neuedu.his.model.dto.ScheduleSourceCreateDTO;
import com.neuedu.his.model.dto.ScheduleSourceQueryDTO;
import com.neuedu.his.model.dto.ScheduleStatusUpdateDTO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleSourceVO;
import com.neuedu.his.service.ScheduleService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/schedule")
public class ScheduleController {

    @Autowired
    private ScheduleService scheduleService;

    @GetMapping("/sources")
    public PageResult<ScheduleSourceVO> getSources(@Valid ScheduleSourceQueryDTO query) {
        return scheduleService.getSources(query);
    }

    @PostMapping("/sources")
    public Integer createSource(@RequestBody @Valid ScheduleSourceCreateDTO request) {
        return scheduleService.createSource(request);
    }

    @PutMapping("/sources/{scheduleId}/quota")
    public void updateQuota(@PathVariable Integer scheduleId,
                            @RequestBody @Valid ScheduleQuotaUpdateDTO request) {
        scheduleService.updateQuota(scheduleId, request);
    }

    @PutMapping("/sources/{scheduleId}/suspend")
    public void suspend(@PathVariable Integer scheduleId,
                        @RequestBody(required = false) ScheduleStatusUpdateDTO request) {
        scheduleService.suspend(scheduleId);
    }

    @PutMapping("/sources/{scheduleId}/resume")
    public void resume(@PathVariable Integer scheduleId,
                       @RequestBody(required = false) ScheduleStatusUpdateDTO request) {
        scheduleService.resume(scheduleId);
    }
}
