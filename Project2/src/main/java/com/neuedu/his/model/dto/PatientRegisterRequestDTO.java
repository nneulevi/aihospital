package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class PatientRegisterRequestDTO {
    @NotBlank(message = "姓名不能为空")
    @Size(max = 64, message = "姓名长度不能超过64个字符")
    private String realName;

    @NotBlank(message = "性别不能为空")
    @Pattern(regexp = "^(男|女|M|F)$", message = "性别只能为男、女、M 或 F")
    private String gender;

    @NotBlank(message = "身份证号不能为空")
    @Pattern(regexp = "^\\d{17}[\\dXx]$", message = "身份证号格式不正确")
    private String cardNumber;

    @NotNull(message = "出生日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate birthdate;

    @NotBlank(message = "家庭住址不能为空")
    private String homeAddress;

    private String phone;

    @NotNull(message = "科室ID不能为空")
    private Integer deptId;

    @NotNull(message = "医生ID不能为空")
    private Integer doctorId;

    @NotNull(message = "看诊日期不能为空")
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate visitDate;

    @NotBlank(message = "午别不能为空")
    private String noon;

    @NotNull(message = "挂号级别不能为空")
    private Integer registLevelId;

    @NotNull(message = "结算类别不能为空")
    private Integer settleCategoryId;

    private String registMethod;
}
