package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ReportGenerateRequestDTO {
    @NotNull(message = "检查申请ID不能为空")
    private Integer checkRequestId;
    
    @NotBlank(message = "报告类型不能为空")
    private String reportType;
    
    private String rawData;
}