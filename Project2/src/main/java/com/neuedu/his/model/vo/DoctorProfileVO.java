package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorProfileVO {
    private Integer id;
    private String realname;
    private String titleLevel;
    private String phone;
    private String roleType;
    private Integer deptmentId;
    private String deptName;
    private Boolean delmark;
    private String createTime;
}