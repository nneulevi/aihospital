package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientListVO {
    private Integer patientId;
    private String realName;
    private String caseNumber;
    private String phone;
    private String gender;
}
