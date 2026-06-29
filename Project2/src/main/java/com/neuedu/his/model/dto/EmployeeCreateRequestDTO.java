package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class EmployeeCreateRequestDTO {

    @NotBlank(message = "姓名不能为空")
    private String realname;

    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    private String password;

    @NotBlank(message = "角色类型不能为空")
    private String roleType;  // DOCTOR / ADMIN

    private Integer deptmentId;  // 医生必填

    private String titleLevel;

    private Boolean enabled;  // true=启用, false=禁用
}