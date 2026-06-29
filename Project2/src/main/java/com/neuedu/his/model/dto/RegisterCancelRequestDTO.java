package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class RegisterCancelRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;
    
    private String cancelReason;
}