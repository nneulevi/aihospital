package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class AiImageAnalysis {
    private Integer id;
    private Integer checkRequestId;
    private Integer registerId;
    private String filePath;
    private String aiFindings;
    private String aiAnnotation;
    private String aiConclusion;
    private BigDecimal confidence;
    private LocalDateTime analysisTime;
    private String aiModelVersion;
    private Short isReviewed;
    private Integer reviewedBy;
    private LocalDateTime reviewedTime;
    private LocalDateTime createTime;
}