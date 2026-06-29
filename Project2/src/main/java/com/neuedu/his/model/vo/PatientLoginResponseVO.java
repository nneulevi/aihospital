package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientLoginResponseVO {
    private String token;
    private Integer patientId;
    private String caseNumber;
    private String realName;
    private Boolean isNewPatient;  // 是否新注册
}