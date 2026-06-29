package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
public class DiagnosisConfirmRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;
    
    @NotBlank(message = "诊断结果不能为空")
    private String diagnosis;
    
    private String cure;
    
    private List<Integer> diseaseIds;
}