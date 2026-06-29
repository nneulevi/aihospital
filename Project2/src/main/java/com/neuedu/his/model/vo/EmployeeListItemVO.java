package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class EmployeeListItemVO {
    private Integer id;
    private String realname;
    private String roleType;
    private String titleLevel;
    private String phone;
    private Integer deptmentId;
    private String deptName;
    private Boolean delmark;
    private String createTime;
}