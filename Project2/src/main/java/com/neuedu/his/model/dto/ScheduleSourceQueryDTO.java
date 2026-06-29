package com.neuedu.his.model.dto;

import lombok.Data;

import java.time.LocalDate;

@Data
public class ScheduleSourceQueryDTO {
    private Integer deptId;
    private Integer doctorId;
    private LocalDate startDate;
    private LocalDate endDate;
    private Integer pageNum = 1;
    private Integer pageSize = 10;
}
