package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class DrugStockRecord {
    private Integer id;
    private Integer drugId;
    private String recordType;
    private Integer quantity;
    private Integer beforeStock;
    private Integer afterStock;
    private Integer operatorId;
    private Integer relatedPrescriptionId;
    private String reason;
    private LocalDateTime createTime;
}
