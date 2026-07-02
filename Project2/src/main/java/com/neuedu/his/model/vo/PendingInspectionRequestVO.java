package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * 患者端待预约检验项目VO
 */
@Data
public class PendingInspectionRequestVO {
    private Integer id;                    // 检验申请ID
    private Integer registerId;            // 挂号记录ID
    private Integer medicalTechnologyId;   // 检验项目ID
    private String techName;               // 项目名称
    private String inspectionInfo;         // 检验信息
    private String inspectionPosition;     // 检验部位
    private BigDecimal techPrice;          // 价格
    private LocalDateTime creationTime;    // 申请时间
}
