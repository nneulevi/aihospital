package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class StaffCreateRequestDTO {
    private Integer deptId;
    private Integer registLevelId;

    @NotBlank(message = "姓名不能为空")
    private String name;

    @NotBlank(message = "账号不能为空")
    private String account;

    @NotBlank(message = "角色不能为空")
    @Pattern(regexp = "DOCTOR|MEDICAL_TECH|DRUGSTORE|PHARMACIST|ADMIN", message = "角色类型不支持")
    private String role;

    private String titleLevel;
    private String phone;
    private String note;
}
