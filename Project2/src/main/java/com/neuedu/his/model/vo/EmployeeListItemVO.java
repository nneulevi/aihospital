package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class EmployeeListItemVO {
    private Integer employeeId;
    private String realname;
    private String roleType;
    private String titleLevel;
    private String phone;
    private Integer deptId;
    private String deptName;
    private Boolean active;
    private LocalDateTime createTime;
}
