package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
public class DisposalRequestCreateDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;
    
    @NotEmpty(message = "处置项目不能为空")
    private List<DisposalItemDTO> items;
    
    @Data
    public static class DisposalItemDTO {
        @NotNull(message = "医技项目ID不能为空")
        private Integer medicalTechnologyId;
        
        private String disposalInfo;
        private String disposalPosition;
    }
}