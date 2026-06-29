package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class PatientRecordListVO {
    private Integer registerId;
    private String visitDate;
    private String deptName;
    private String doctorName;
    private String diagnosis;
    private String visitState;
    private String visitStateName;

    // ===== 新增字段 =====
    private String noon;
    private Integer queueNumber;
    private Integer checkinStatus;
    private BigDecimal registFee;
    private Integer deptId;
    private Integer doctorId;
    private String patientName;
    private String gender;
    private Integer age;
    private String allergyHistory;
    private String caseNumber;
}