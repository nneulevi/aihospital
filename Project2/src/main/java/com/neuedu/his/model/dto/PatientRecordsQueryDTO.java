package com.neuedu.his.model.dto;

import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class PatientRecordsQueryDTO extends PageQueryDTO {
    private Integer patientId;
    
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate startDate;
    
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate endDate;
    
    private String visitState;
}