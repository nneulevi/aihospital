package com.neuedu.his.model.dto;



import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

/**
 * 患者注册/添加就诊人 请求DTO
 * 用于：手机号验证码注册、添加就诊人
 */
@Data
public class PatientAuthRegisterRequestDTO {

    @NotBlank(message = "姓名不能为空")
    private String realName;

    @NotBlank(message = "身份证号不能为空")
    @Pattern(regexp = "^\\d{17}[\\dXx]$", message = "身份证号格式不正确")
    private String cardNumber;

    @NotBlank(message = "手机号不能为空")
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "手机号格式不正确")
    private String phone;

    @NotBlank(message = "验证码不能为空")
    private String code;

    private String gender;
    private String birthdate;   // 接收字符串 "1990-03-07"
    private String homeAddress;
}