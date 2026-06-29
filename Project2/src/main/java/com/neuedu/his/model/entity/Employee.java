package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Employee {
    private Integer id;
    private Integer deptmentId;
    private Integer registLevelId;
    private String realname;
    private String roleType;
    private String titleLevel;
    private String passwordHash;
    private String phone;
    private Boolean delmark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}