package com.neuedu.his.model.vo;

import lombok.Data;
import java.time.LocalDate;

@Data
public class PatientListVO {
    private Integer id;
    private String caseNumber;
    private String realName;
    private String gender;
    private String phone;
    private Boolean isDefault;

    // ===== 新增字段 =====
    private String cardNumber;
    private LocalDate birthdate;
    private String homeAddress;
    private String relation;
    private Integer age;  // 由后端计算
}