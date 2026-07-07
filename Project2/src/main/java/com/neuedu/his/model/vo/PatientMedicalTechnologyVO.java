package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class PatientMedicalTechnologyVO {
    private Integer techId;
    private String techCode;
    private String techName;
    private String techFormat;
    private BigDecimal techPrice;
    private String techType;
    private String priceType;
    private Integer deptId;
    private String deptName;
}
