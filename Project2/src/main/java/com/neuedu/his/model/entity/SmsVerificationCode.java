package com.neuedu.his.model.entity;


import lombok.Data;
import java.time.LocalDateTime;

@Data
public class SmsVerificationCode {
    private Long id;
    private String phone;
    private String code;
    private String type;        // REGISTER, LOGIN, BIND
    private LocalDateTime expiredAt;
    private Boolean used;
    private LocalDateTime createdAt;
}