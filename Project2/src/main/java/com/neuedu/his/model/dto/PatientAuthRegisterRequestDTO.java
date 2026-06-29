package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class PatientAuthRegisterRequestDTO {
    @NotBlank(message = "realName is required")
    @Size(max = 64, message = "realName length must be <= 64")
    private String realName;

    @NotBlank(message = "cardNumber is required")
    @Pattern(regexp = "^\\d{17}[\\dXx]$", message = "cardNumber format is invalid")
    private String cardNumber;

    @NotBlank(message = "phone is required")
    @Pattern(regexp = "^1[3-9]\\d{9}$", message = "phone format is invalid")
    private String phone;

    @NotBlank(message = "code is required")
    private String code;

    private String gender;

    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate birthdate;

    private String homeAddress;
}
