package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;

@Data
public class DoctorPatientsQueryDTO extends PageQueryDTO {
    @NotNull(message = "医生ID不能为空")
    private Integer doctorId;
    
    private String visitState; // REGISTERED/DOCTOR_RECEIVED
}