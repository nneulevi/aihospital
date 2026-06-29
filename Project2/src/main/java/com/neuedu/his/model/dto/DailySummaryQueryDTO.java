package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class DailySummaryQueryDTO {
    @NotNull(message = "日结日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate summaryDate;
    
    private Integer operatorId;
}