package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AiScheduleRule {
    private Integer id;
    private String ruleName;
    private Integer deptmentId;
    private String ruleConfig;
    private String constraintJson;
    private Boolean isActive;
    private String aiModelVersion;
    private LocalDateTime createdTime;
    private LocalDateTime updatedTime;
}