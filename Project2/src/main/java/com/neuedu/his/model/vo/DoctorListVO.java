package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDate;

@Data
public class DoctorListVO {
    private Integer doctorId;
    private String doctorName;
    private String titleLevel;
    private LocalDate scheduleDate;
    private String noon;
    private Integer registQuota;
    private Integer remainingQuota;

    // ===== 新增字段 =====
    private String deptName;
    private BigDecimal registFee;
}