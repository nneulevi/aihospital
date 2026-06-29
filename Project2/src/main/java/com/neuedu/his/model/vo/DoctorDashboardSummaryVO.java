package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorDashboardSummaryVO {
    private Integer doctorId;
    private Long pendingCount;
    private Long consultingCount;
    private Long finishedToday;
    private Long pendingCheckCount;
}
