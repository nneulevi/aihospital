package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorStatisticsVO {
    private Integer todayVisits;
    private Integer monthVisits;
    private Integer totalVisits;
    private Integer pendingCount;
    private Integer consultingCount;
    private Integer finishedCount;
}