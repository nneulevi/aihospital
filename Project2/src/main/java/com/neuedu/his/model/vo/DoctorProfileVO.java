package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class DoctorProfileVO {
    private Integer doctorId;
    private String doctorName;
    private String titleLevel;
    private String phone;
    private String roleType;
    private Integer deptId;
    private String deptName;
    private Boolean active;
    private LocalDateTime createTime;
}
