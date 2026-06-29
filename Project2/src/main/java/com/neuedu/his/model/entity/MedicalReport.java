package com.neuedu.his.model.entity;

import lombok.Data;
import java.time.LocalDateTime;

@Data
public class MedicalReport {
    private Long id;
    private Long registerId;
    private Long patientId;
    private String requestType;
    private Long requestId;
    private String reportTitle;
    private String reportText;
    private String reportFileUrl;
    private LocalDateTime reportTime;
    private Integer isViewed;
    private LocalDateTime viewedTime;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}