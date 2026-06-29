package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class AdminDashboardSummaryVO {
    private Long todayRegistrations;
    private Long activePatients;
    private BigDecimal pendingChargeAmount;
    private Long stockAlertCount;
    private Long todayAiAnalysisCount;
    private Long pendingReportCount;
}
