package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class DrugRefundRequestDTO {
    @NotNull(message = "处方ID不能为空")
    private Integer prescriptionId;
    
    @NotNull(message = "退药员ID不能为空")
    private Integer pharmacistId;
    
    private String refundReason;
}