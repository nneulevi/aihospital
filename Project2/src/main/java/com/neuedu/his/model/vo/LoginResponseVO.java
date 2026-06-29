package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class LoginResponseVO {
    private String token;
    private Integer employeeId;
    private String realname;
    private String roleType;
    private Integer deptId;
}