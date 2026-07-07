package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Data
public class PrescriptionDetailVO {
    private Integer prescriptionId;
    private Integer registerId;
    private String prescriptionNo;
    private String deptName;
    private String doctorName;
    private String patientName;
    private String status;
    private String statusName;
    private BigDecimal totalAmount;
    private LocalDateTime creationTime;
    private LocalDateTime dispenseTime;
    private List<PrescriptionDrugDetailVO> drugs = new ArrayList<>();

    @Data
    public static class PrescriptionDrugDetailVO {
        private Integer drugId;
        private String drugName;
        private String specification;
        private String dosage;
        private String frequency;
        private Integer days;
        private Integer quantity;
        private BigDecimal price;
    }
}
