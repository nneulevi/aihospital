package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 患者端待预约检验列表查询DTO
 */
@Data
public class InspectionRequestQueryDTO {
    @NotNull(message = "患者ID不能为空")
    private Integer patientId;
}
