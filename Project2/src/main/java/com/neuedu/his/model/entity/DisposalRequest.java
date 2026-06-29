package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class DisposalRequest {
    private Integer id;
    private Integer registerId;
    private Integer medicalTechnologyId;
    private String disposalInfo;
    private String disposalPosition;
    private LocalDateTime creationTime;
    private Integer disposalEmployeeId;
    private Integer inputdisposalEmployeeId;
    private LocalDateTime disposalTime;
    private String disposalResult;
    private String disposalState;
    private String disposalRemark;
}