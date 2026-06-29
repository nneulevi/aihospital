package com.neuedu.his.model.vo;

import lombok.Data;

/**
 * 当前患者信息VO
 */
@Data
public class PatientCurrentVO {
    private Integer patientId;
    private String realName;
    private String phone;
    private String caseNumber;
}