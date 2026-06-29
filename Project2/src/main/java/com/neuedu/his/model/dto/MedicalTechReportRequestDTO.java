package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class MedicalTechReportRequestDTO {
    @NotNull
    private Integer reporterId;
    @NotBlank
    private String result;
    private String remark;
}
