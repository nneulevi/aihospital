package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ImageAnalyzeRequestDTO {
    @NotNull(message = "影像文件ID不能为空")
    private Integer imageFileId;
    
    @NotNull(message = "检查申请ID不能为空")
    private Integer checkRequestId;
}