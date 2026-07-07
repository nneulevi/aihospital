package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDate;

@Data
public class ScheduleResultVO {
    private Integer id;
    private Integer deptId;
    private Integer doctorId;
    private String doctorName;
    private LocalDate scheduleDate;
    private String shiftType;
    private Integer registQuota;
    private Short isGenerated;
    private Short isModified;
    private String sourceType;
}
