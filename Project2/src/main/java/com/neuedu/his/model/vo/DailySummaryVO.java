package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class DailySummaryVO {
    private LocalDate summaryDate;
    private Integer totalTransactions;
    private BigDecimal totalAmount;
    private BigDecimal refundAmount;
    private Integer chargeCount;
    private Integer refundCount;
    private String operatorName;
}