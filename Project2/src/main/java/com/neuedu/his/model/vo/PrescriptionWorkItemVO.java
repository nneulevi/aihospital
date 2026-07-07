package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class PrescriptionWorkItemVO {
    private Integer prescriptionId;
    private Integer registerId;
    private String prescriptionNo;
    private String patientName;
    private String doctorName;
    private String status;
    private String statusName;
    private BigDecimal totalAmount;
    private String drugSummary;
    private LocalDateTime creationTime;
    private LocalDateTime dispenseTime;
}
