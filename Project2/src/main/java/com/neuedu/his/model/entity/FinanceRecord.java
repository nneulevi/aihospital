

package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;


@Data
public class FinanceRecord {
    private Long id;
    private String recordNo;
    private Long registerId;
    private String recordType; // CHARGE/REFUND
    private BigDecimal totalAmount;
    private Integer itemCount;
    private String chargeMethod;
    private Integer operatorId;
    private LocalDateTime createTime;
}