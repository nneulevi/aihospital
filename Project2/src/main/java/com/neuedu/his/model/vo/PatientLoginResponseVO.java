package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientLoginResponseVO {
    private String token;
    private Integer patientId;
    private String caseNumber;
    private String realName;
    private String cardNumber;      // 🔥 新增
    private String phone;           // 🔥 新增
    private String gender;          // 🔥 新增
    private String birthdate;       // 🔥 新增
    private String homeAddress;     // 🔥 新增
    private Boolean isNewPatient;
}