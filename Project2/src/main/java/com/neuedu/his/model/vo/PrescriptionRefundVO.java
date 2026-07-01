package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.util.List;

@Data
public class PrescriptionRefundVO {
    private Integer prescriptionId;
    private String prescriptionNo;
    private String patientName;
    private List<String> drugList;
    private BigDecimal totalAmount;
    private String status;
}
