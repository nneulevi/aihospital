package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DeptQueueVO {
    private Integer deptId;
    private String deptName;
    private Integer activeQueueCount;
}
