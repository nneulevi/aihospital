package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class PatientMedicalRequestVO {
    private Integer requestId;
    private Integer registerId;
    private String itemType;
    private String itemName;
    private String itemPosition;
    private String state;
    private String stateName;
    private String result;
    private BigDecimal price;
    private LocalDateTime creationTime;
}
