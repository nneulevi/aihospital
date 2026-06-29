package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class DrugInfo {
    private Integer id;
    private String drugCode;
    private String drugName;
    private String drugFormat;
    private String drugUnit;
    private String manufacturer;
    private String drugDosage;
    private String drugType;
    private BigDecimal drugPrice;
    private Integer stockNum;
    private String mnemonicCode;
    private LocalDate creationDate;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}