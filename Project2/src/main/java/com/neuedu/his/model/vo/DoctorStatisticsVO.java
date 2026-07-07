package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorStatisticsVO {
    private Long todayVisits;
    private Long monthVisits;
    private Long totalVisits;
    private Long pendingCount;
    private Long consultingCount;
    private Long finishedCount;
    private Long pendingCheckCount;
}
