package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import lombok.Data;

@Data
public class SendCodeRequestDTO {
    @NotBlank(message = "phone is required")
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "phone format is invalid")
    private String phone;

    private String codeType;
}
