package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AiDiagnosisSuggestion {
    private Integer id;
    private Integer medicalRecordId;
    private Integer registerId;
    private String aiDiagnosis;
    private Integer diseaseId;
    private BigDecimal confidence;
    private String evidenceBasis;
    private String doctorFeedback;
    private LocalDateTime suggestionTime;
    private String aiModelVersion;
    private Boolean isAdopted;
    private LocalDateTime createTime;
}