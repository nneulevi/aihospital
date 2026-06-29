package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class DrugInventoryVO {
    private Integer drugId;
    private String drugCode;
    private String drugName;
    private String drugFormat;
    private String drugUnit;
    private Integer stockNum;
    private BigDecimal drugPrice;
    private Boolean alert;
    private String manufacturer;
}