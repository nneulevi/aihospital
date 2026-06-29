package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.List;

/**
 * 处方详情VO
 */
@Data
public class PrescriptionDetailVO {
    private Integer id;
    private String prescriptionNo;
    private String deptName;
    private String doctorName;
    private String patientName;
    private String status;
    private BigDecimal totalAmount;
    private LocalDateTime creationTime;
    // private String remark;  // 删除这行
    private List<PrescriptionDrugDetailVO> drugs;

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