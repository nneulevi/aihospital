package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class FinanceRecordVO {
    private Integer id;
    private String recordNo;
    private Integer registerId;
    private String patientName;
    private Integer itemId;
    private String itemType;
    private String itemName;
    private BigDecimal amount;
    private String chargeMethod;
    private String recordType;
    private LocalDateTime createTime;
    private String operatorName;
}
