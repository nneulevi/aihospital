package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class PatientRegisterRequestDTO {

    // ===== 新增：患者ID =====
    @NotNull(message = "就诊人ID不能为空")
    private Integer patientId;

    @NotNull(message = "科室ID不能为空")
    private Integer deptId;

    @NotNull(message = "医生ID不能为空")
    private Integer doctorId;

    @NotNull(message = "看诊日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate visitDate;

    @NotBlank(message = "午别不能为空")
    private String noon;

    // ===== 可选字段（有默认值） =====
    private Integer registLevelId;    // 默认取医生的挂号级别
    private Integer settleCategoryId; // 默认取"自费"
    private String registMethod;      // 默认"在线预约"


}