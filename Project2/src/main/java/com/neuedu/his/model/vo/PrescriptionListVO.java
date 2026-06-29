package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 处方列表VO
 */
@Data
public class PrescriptionListVO {
    private Integer id;
    private String prescriptionNo;
    private String deptName;
    private String doctorName;
    private String patientName;
    private String status;      // ACTIVE / COMPLETED / CANCELLED
    private BigDecimal totalAmount;
    private LocalDateTime creationTime;
    private List<PrescriptionDrugSummaryVO> drugs;

    @Data
    public static class PrescriptionDrugSummaryVO {
        private Integer drugId;
        private String drugName;
    }
}