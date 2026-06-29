package com.neuedu.his.model.vo;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class ImageAnalyzeResponseVO {
    private Integer analysisId;
    private String findings;
    private String conclusion;
    private Double confidence;
    private List<Annotation> annotations;
    private Map<String, Object> aiImagingStatus;

    @Data
    public static class Annotation {
        private Integer x;
        private Integer y;
        private Integer width;
        private Integer height;
        private String label;
    }
}
