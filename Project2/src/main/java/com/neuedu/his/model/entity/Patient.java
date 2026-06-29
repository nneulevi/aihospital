package com.neuedu.his.model.entity;


import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class Patient {
    private Integer id;
    private String caseNumber;
    private String realName;
    private String gender;
    private String cardNumber;
    private LocalDate birthdate;
    private String phone;
    private String homeAddress;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;

    // ========== 新增字段 ==========
    private Boolean phoneVerified;     // 手机号是否已验证
    private LocalDateTime lastLoginTime; // 最后登录时间
}