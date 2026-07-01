
package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class DrugRefund {
    private Long id;
    private Long prescriptionId;
    private Integer pharmacistId;
    private String refundReason;
    private BigDecimal refundAmount;
    private LocalDateTime refundTime;
    private LocalDateTime createTime;
}
