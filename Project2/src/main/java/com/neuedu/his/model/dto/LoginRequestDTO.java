package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class LoginRequestDTO {
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    private String username;

    @Size(min = 6, max = 20, message = "密码长度6-20位")
    private String password;

    @Size(min = 4, max = 6, message = "验证码长度4-6位")
    private String verifyCode;

    @NotBlank(message = "登录类型不能为空")
    private String loginType; // PATIENT / DOCTOR / ADMIN
}