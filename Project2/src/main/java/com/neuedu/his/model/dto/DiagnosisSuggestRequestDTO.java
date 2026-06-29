package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class DiagnosisSuggestRequestDTO {
    @NotNull(message = "病历ID不能为空")
    private Integer medicalRecordId;
    
    private String symptoms;
    private String history;
    private String physique;
}