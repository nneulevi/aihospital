package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

/**
 * 报到提交请求DTO
 */
@Data
public class CheckinRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;
}