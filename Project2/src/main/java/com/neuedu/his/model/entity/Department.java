package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Department {
    private Integer id;
    private String deptCode;
    private String deptName;
    private String deptType;
    private Boolean delmark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}