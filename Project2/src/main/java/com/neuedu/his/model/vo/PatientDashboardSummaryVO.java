package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class PatientDashboardSummaryVO {
    private Integer patientId;
    private Long recordCount;
    private Long unpaidOrderCount;
    private BigDecimal unpaidAmount;
    private String latestVisitState;
}
