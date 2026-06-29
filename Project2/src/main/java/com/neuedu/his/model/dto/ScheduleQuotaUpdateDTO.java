package com.neuedu.his.model.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class ScheduleQuotaUpdateDTO {
    @NotNull
    @Min(0)
    private Integer registQuota;
}
