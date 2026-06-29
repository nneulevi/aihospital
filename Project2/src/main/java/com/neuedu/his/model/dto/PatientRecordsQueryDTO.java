package com.neuedu.his.model.dto;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class PatientRecordsQueryDTO extends PageQueryDTO {
    private Integer patientId;

    // ===== 新增：按状态筛选 =====
    private String visitState;  // REGISTERED / CONSULTING / FINISHED / CANCELLED
}