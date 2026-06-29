package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class Prescription {
    private Integer id;
    private Integer registerId;
    private Integer doctorId;
    private String prescriptionNo;
    private BigDecimal totalAmount;
    private String prescriptionStatus;
    private LocalDateTime creationTime;
    private LocalDateTime updateTime;
    private LocalDateTime dispenseTime;
    private Integer pharmacistId;
}