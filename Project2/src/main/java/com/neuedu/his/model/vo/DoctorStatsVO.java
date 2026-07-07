package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorStatsVO {
    private Integer doctorId;
    private String doctorName;
    private String deptName;
    private String titleLevel;
    private Long todayRegistrations;
    private Long activePatients;
    private Long finishedToday;
    private Long pendingChecks;
}
