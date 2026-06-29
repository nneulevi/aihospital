package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class AiScheduleResult {
    private Integer id;
    private Integer employeeId;
    private Integer deptmentId;
    private LocalDate scheduleDate;
    private String shiftType;
    private Integer registQuota;
    private Short isGenerated;
    private Short isModified;
    private String sourceType;
    private LocalDateTime createdTime;
    private LocalDateTime updateTime;
}