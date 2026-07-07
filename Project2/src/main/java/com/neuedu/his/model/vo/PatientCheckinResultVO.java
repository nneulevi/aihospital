package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientCheckinResultVO {
    private Integer registerId;
    private String visitState;
    private String visitStateName;
    private Integer queueNo;
    private String deptName;
    private String doctorName;
    private String message;
}
