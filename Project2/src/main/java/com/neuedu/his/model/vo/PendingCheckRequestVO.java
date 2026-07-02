package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 患者端待预约检查项目VO
 */
@Data
public class PendingCheckRequestVO {
    private Integer id;                    // 检查申请ID
    private Integer registerId;            // 挂号记录ID
    private Integer medicalTechnologyId;   // 检查项目ID
    private String techName;               // 项目名称
    private String checkInfo;              // 检查信息
    private String checkPosition;          // 检查部位
    private BigDecimal techPrice;          // 价格
    private LocalDateTime creationTime;    // 申请时间
}
