package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDate;

@Data
public class DoctorListVO {
    private Integer doctorId;
    private Integer deptId;
    private String deptName;
    private String doctorName;
    private String titleLevel;
    private String specialty;
    private LocalDate scheduleDate;
    private String noon;
    private Integer registQuota;
    private Integer remainingQuota;
}
