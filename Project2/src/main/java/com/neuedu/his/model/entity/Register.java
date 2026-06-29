package com.neuedu.his.model.entity;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Data
public class Register {
    private Integer id;
    private String visitNo;
    private Integer patientId;
    private LocalDateTime visitDate;
    private String noon;
    private Integer deptmentId;
    private Integer employeeId;
    private Integer registLevelId;
    private Integer settleCategoryId;
    private String sourceType;
    private Integer queueNo;
    private String registMethod;
    private BigDecimal registMoney;
    private String visitState;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
    // 新增
    private Integer age;
    private String deptName;      // 科室名称
    private String doctorName;    // 医生姓名
    private String registName;    // 挂号级别名称
    private String realName;      // 患者姓名
    private String gender;        // 患者性别
    private LocalDate birthdate;  // 患者出生日期
    // ========== 新增字段 ==========
    private Integer checkinStatus;   // 0-未报到 1-已报到
    private LocalDateTime checkinTime; // 报到时间
}