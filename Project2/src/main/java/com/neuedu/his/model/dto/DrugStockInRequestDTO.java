package com.neuedu.his.model.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class DrugStockInRequestDTO {
    @NotNull
    private Integer drugId;
    @NotNull
    @Min(1)
    private Integer quantity;
    @NotNull
    private Integer operatorId;
    private String reason;
}
