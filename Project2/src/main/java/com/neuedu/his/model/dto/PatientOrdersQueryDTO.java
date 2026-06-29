package com.neuedu.his.model.dto;

import lombok.Data;

@Data
public class PatientOrdersQueryDTO extends PageQueryDTO {
    private Integer patientId;
    
    private String orderState; // UNPAID/PAID/REFUNDED
}