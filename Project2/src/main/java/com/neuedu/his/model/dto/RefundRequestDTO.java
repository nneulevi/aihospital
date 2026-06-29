package com.neuedu.his.model.dto;

import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class RefundRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotEmpty(message = "退费项目不能为空")
    private List<Integer> itemIds;

    @DecimalMin(value = "0.01", message = "金额必须大于0")
    private BigDecimal refundAmount;

    private String refundReason;
}