package com.neuedu.his.model.vo;

import lombok.Data;

import java.util.List;

@Data
public class DiagnosisSuggestResponseVO {
    private List<Suggestion> suggestions;

    @Data
    public static class Suggestion {
        private String diseaseName;
        private String diseaseCode;
        private Double confidence;
        private String evidence;
    }
}