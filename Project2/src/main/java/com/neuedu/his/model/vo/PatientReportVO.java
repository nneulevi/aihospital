package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class PatientReportVO {
    private String reportId;
    private Integer registerId;
    private String itemType;
    private Integer itemId;
    private String itemName;
    private String itemPosition;
    private String status;
    private String statusName;
    private String result;
    private String deptName;
    private String doctorName;
    private LocalDateTime reportTime;
    private LocalDateTime creationTime;
}
