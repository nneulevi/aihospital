package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDateTime;
import java.util.List;

/**
 * 患者端检验预约提交DTO
 */
@Data
public class PatientInspectionRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotNull(message = "患者ID不能为空")
    private Integer patientId;

    @NotNull(message = "检验项目ID不能为空")
    private List<Integer> medicalTechnologyIds;

    @NotNull(message = "预约时间不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime bookedTime;
}