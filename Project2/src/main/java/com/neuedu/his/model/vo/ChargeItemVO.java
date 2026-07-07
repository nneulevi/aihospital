package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class ChargeItemVO {
    private Integer itemId;
    private String itemType;
    private String itemName;
    private Integer registerId;
    private String patientName;
    private BigDecimal amount;
    private String state;
    private String stateName;
    private LocalDateTime creationTime;
}
