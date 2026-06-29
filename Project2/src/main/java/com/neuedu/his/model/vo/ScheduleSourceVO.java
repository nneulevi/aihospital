package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDate;

@Data
public class ScheduleSourceVO {
    private Integer scheduleId;
    private Integer doctorId;
    private String doctorName;
    private Integer deptId;
    private String deptName;
    private LocalDate scheduleDate;
    private String noon;
    private Integer registQuota;
    private String scheduleStatus;
    private String sourceType;
}
