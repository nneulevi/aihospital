package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class PatientInspectionRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotNull(message = "患者ID不能为空")
    private Integer patientId;

    @NotEmpty(message = "检验项目不能为空")
    private List<Integer> medicalTechnologyIds;

    private LocalDateTime bookedTime;
}
