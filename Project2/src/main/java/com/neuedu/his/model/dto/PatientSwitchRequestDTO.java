package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class PatientSwitchRequestDTO {

    @NotNull(message = "就诊人ID不能为空")
    private Integer patientId;
}