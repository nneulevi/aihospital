package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class PatientRecordListVO {
    private Integer registerId;
    private String visitDate;
    private String deptName;
    private String doctorName;
    private String diagnosis;
    private String visitState;
    private String visitStateName;
}