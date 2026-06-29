package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorPatientListVO {
    private Integer registerId;
    private String caseNumber;
    private String patientName;
    private String gender;
    private Integer age;
    private String registrationTime;
    private String noon;
    private String visitState;
}
