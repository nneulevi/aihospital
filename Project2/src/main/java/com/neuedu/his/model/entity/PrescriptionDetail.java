package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class PrescriptionDetail {
    private Integer id;
    private Integer prescriptionId;
    private Integer drugId;
    private String usageRoute;
    private String frequency;
    private String singleDose;
    private Integer useDays;
    private Integer drugNumber;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}