package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

@Data
public class PatientPrescriptionVO {
    private Integer prescriptionId;
    private Integer registerId;
    private String prescriptionNo;
    private String status;
    private String statusName;
    private BigDecimal totalAmount;
    private String doctorName;
    private LocalDateTime creationTime;
    private LocalDateTime dispenseTime;
    private List<String> drugNames;
    private String drugSummary;
}
