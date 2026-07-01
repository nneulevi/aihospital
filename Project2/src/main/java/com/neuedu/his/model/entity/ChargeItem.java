package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;


@Data
public class ChargeItem {
    private Long id;
    private Long sourceId;
    private String sourceType;
    private Long registerId;
    private String itemName;
    private String itemType;
    private BigDecimal amount;
    private String status; // PENDING/CHARGED/REFUNDED
    private Long financeRecordId;
    private String chargeMethod;
    private LocalDateTime chargeTime;
    private String refundReason;
    private LocalDateTime refundTime;
    private Integer operatorId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}