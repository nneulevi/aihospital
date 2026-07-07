package com.neuedu.his.model.dto;

import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDate;

@Data
public class ScheduleSourceCreateDTO {
    @NotNull
    private Integer doctorId;
    @NotNull
    private Integer deptId;
    @NotNull
    private LocalDate scheduleDate;
    @NotNull
    private String noon;
    @NotNull
    @Min(1)
    private Integer registQuota;
    private String sourceType = "MANUAL";
}
