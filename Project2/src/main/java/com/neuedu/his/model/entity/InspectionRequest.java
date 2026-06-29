package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class InspectionRequest {
    private Integer id;
    private Integer registerId;
    private Integer medicalTechnologyId;
    private String inspectionInfo;
    private String inspectionPosition;
    private LocalDateTime creationTime;
    private Integer inspectionEmployeeId;
    private Integer inputinspectionEmployeeId;
    private LocalDateTime inspectionTime;
    private String inspectionResult;
    private String inspectionState;
    private String inspectionRemark;
    // ========== 新增字段 ==========
    private Integer isSelfBooked;    // 0-医生开单 1-患者自助预约
    private LocalDateTime bookedTime; // 预约时间
}