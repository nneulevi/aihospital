package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import lombok.Data;
import org.springframework.format.annotation.DateTimeFormat;

import java.time.LocalDate;

@Data
public class DoctorListQueryDTO extends PageQueryDTO {
    @NotNull(message = "科室ID不能为空")
    private Integer deptId;
    
    @DateTimeFormat(pattern = "yyyy-MM-dd")
    private LocalDate visitDate;
    
    private String noon;
}