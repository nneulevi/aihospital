package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class PatientTodayRegisterVO {
    private Integer registerId;
    private String visitNo;
    private Integer patientId;
    private LocalDate visitDate;
    private String noon;
    private Integer queueNo;
    private String visitState;
    private String visitStateName;
    private String deptName;
    private String doctorName;
    private LocalDateTime createTime;
}
