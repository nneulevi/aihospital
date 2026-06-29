package com.neuedu.his.model.dto;

import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class ReportQueryDTO extends PageQueryDTO {
    private Long patientId;
    private String requestType;
}