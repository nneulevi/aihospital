package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DepartmentStatsVO {
    private Integer deptId;
    private String deptName;
    private String deptType;
    private Long doctorCount;
    private Long todayRegistrations;
    private Long activePatients;
    private Long scheduleQuota;
    private Long pendingChecks;
}
