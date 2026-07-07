package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientCurrentVO {
    private Integer patientId;
    private String realName;
    private String phone;
    private String caseNumber;
}
