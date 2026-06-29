package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AiConsultation {
    private Integer id;
    private Integer patientId;
    private Integer registerId;
    private String symptomsDesc;
    private String aiRecommendDept;
    private String aiDiagnosisHint;
    private LocalDateTime consultationTime;
    private String aiModelVersion;
    private Short status;
    private LocalDateTime createTime;
}