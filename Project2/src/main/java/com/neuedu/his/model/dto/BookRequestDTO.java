package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;

/**
 * 患者端预约（检查/检验）请求DTO
 */
@Data
public class BookRequestDTO {
    @NotNull(message = "申请记录ID不能为空")
    private Integer requestId;

    @NotNull(message = "预约时间不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime bookedTime;
}
