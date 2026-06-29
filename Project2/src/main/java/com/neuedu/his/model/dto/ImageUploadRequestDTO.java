package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ImageUploadRequestDTO {
    @NotNull(message = "检查申请ID不能为空")
    private Integer checkRequestId;
    
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;
}