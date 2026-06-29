package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class ConsultationRequestDTO {
    @NotBlank(message = "症状描述不能为空")
    private String symptoms;
    
    private Integer patientId;
}