package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CheckRequest {
    private Integer id;
    private Integer registerId;
    private Integer medicalTechnologyId;
    private String checkInfo;
    private String checkPosition;
    private LocalDateTime creationTime;
    private Integer checkEmployeeId;
    private Integer inputcheckEmployeeId;
    private LocalDateTime checkTime;
    private String checkResult;
    private String checkState;
    private String checkRemark;
    private Integer isSelfBooked;    // 0-医生开单 1-患者自助预约
    private LocalDateTime bookedTime; // 预约时间
}