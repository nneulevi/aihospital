package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.time.LocalDateTime;

@Data
public class BookRequestDTO {
    @NotNull(message = "申请ID不能为空")
    private Integer requestId;

    @NotNull(message = "预约时间不能为空")
    private LocalDateTime bookedTime;
}
