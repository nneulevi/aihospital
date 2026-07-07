package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class ReportDetailVO {
    private String reportId;
    private Integer registerId;
    private String reportTitle;
    private String requestType;
    private String requestTypeName;
    private String deptName;
    private String doctorName;
    private String patientName;
    private LocalDateTime reportTime;
    private String reportText;
    private Boolean viewed;
    private String reportFileUrl;
}
