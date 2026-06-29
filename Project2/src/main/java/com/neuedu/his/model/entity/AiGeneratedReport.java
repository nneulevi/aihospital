package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AiGeneratedReport {
    private Integer id;
    private Integer requestId;
    private Integer registerId;
    private String reportType;
    private String aiRawContent;
    private String aiStructuredData;
    private String finalContent;
    private String referenceSource;
    private String aiModelVersion;
    private LocalDateTime generationTime;
    private String status;
    private Short isConfirmed;
    private Integer confirmedBy;
    private LocalDateTime confirmedTime;
    private String editHistory;
    private LocalDateTime createTime;
}