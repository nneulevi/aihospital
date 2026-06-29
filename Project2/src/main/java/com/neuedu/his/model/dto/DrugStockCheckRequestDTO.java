package com.neuedu.his.model.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class DrugStockCheckRequestDTO {
    @NotNull
    private Integer drugId;
    @NotNull
    @Min(0)
    private Integer actualStock;
    @NotNull
    private Integer operatorId;
    private String reason;
}
