package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class DrugStockRecordVO {
    private Integer id;
    private Integer drugId;
    private String drugName;
    private String recordType;
    private Integer quantity;
    private Integer beforeStock;
    private Integer afterStock;
    private Integer operatorId;
    private String operatorName;
    private Integer relatedPrescriptionId;
    private String reason;
    private LocalDateTime createTime;
}
