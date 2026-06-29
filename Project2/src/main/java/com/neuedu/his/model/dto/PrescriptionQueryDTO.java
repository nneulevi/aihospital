package com.neuedu.his.model.dto;

import lombok.Data;
import lombok.EqualsAndHashCode;

/**
 * 处方查询DTO
 */
@Data
@EqualsAndHashCode(callSuper = true)
public class PrescriptionQueryDTO extends PageQueryDTO {
    private Integer patientId;
    private String status;  // ACTIVE / COMPLETED / CANCELLED
}