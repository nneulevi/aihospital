package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class MedicalTechnology {
    private Integer id;
    private String techCode;
    private String techName;
    private String techFormat;
    private BigDecimal techPrice;
    private String techType;
    private String priceType;
    private Integer deptmentId;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}