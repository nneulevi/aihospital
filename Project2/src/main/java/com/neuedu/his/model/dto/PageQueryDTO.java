package com.neuedu.his.model.dto;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.Data;

@Data
public class PageQueryDTO {
    @Min(1)
    private Integer pageNum = 1;
    
    @Min(1)
    @Max(50)
    private Integer pageSize = 10;
}