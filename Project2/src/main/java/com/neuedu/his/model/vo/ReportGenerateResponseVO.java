package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class ReportGenerateResponseVO {
    private Integer reportId;
    private String reportContent;
    private String status;
}