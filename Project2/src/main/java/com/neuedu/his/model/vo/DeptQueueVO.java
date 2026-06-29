package com.neuedu.his.model.vo;

import lombok.Data;

/**
 * 候诊科室VO（用于切换科室）
 */
@Data
public class DeptQueueVO {
    private Integer deptId;
    private String deptName;
}