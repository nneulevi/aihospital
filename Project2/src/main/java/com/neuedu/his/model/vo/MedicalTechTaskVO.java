package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class MedicalTechTaskVO {
    private String itemType;
    private Integer itemId;
    private Integer registerId;
    private String patientName;
    private String projectName;
    private String projectPosition;
    private String state;
    private String result;
    private BigDecimal price;
    private LocalDateTime creationTime;
}
