package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class Scheduling {
    private Integer id;
    private Integer employeeId;
    private Integer deptmentId;
    private LocalDate scheduleDate;
    private String noon;
    private Integer registQuota;
    private String scheduleStatus;
    private String sourceType;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}