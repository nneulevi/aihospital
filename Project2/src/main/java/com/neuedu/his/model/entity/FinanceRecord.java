package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class FinanceRecord {
    private Integer id;
    private String recordNo;
    private Integer registerId;
    private Integer itemId;
    private String itemType;
    private String itemName;
    private BigDecimal amount;
    private String chargeMethod;
    private String recordType;
    private String operatorName;
    private LocalDateTime createTime;
}
