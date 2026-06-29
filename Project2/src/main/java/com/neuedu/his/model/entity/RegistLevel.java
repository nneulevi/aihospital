package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class RegistLevel {
    private Integer id;
    private String registCode;
    private String registName;
    private BigDecimal registFee;
    private Integer registQuota;
    private Boolean isExpert;
    private Integer sequenceNo;
    private Boolean delmark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}