package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDate;

@Data
public class PatientQueueStatusVO {
    private Integer registerId;
    private Integer patientId;
    private LocalDate visitDate;
    private String noon;
    private String deptName;
    private String doctorName;
    private Integer queueNo;
    private Integer waitingAhead;
    private String visitState;
    private String visitStateName;
    private String message;
}
