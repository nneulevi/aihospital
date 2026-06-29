package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class MedicalTechExecuteRequestDTO {
    @NotNull
    private Integer executorId;
    private String remark;
}
