package com.neuedu.his.model.vo;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class ReportListVO {
    private Long id;
    private String reportTitle;
    private String requestType;
    private String requestTypeName;
    private String deptName;
    private String patientName;
    private LocalDateTime reportTime;
    private Boolean isViewed;
}