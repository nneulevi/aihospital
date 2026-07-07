package com.neuedu.his.model.vo;

import lombok.Data;

import java.util.List;

@Data
public class ConsultationResponseVO {
    private Integer consultationId;
    private String diagnosisHint;
    private List<DeptRecommendation> recommendations;

    @Data
    public static class DeptRecommendation {
        private Integer deptId;
        private String deptName;
        private Double confidence;
        private String reason;
    }
}
