package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class StaffCreateResponseVO {
    private Integer staffId;
    private String account;
    private String name;
    private String role;
    private String status;
}
