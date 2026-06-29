package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
public class OrderListVO {
    private Integer registerId;
    private String itemType;
    private String itemName;
    private Integer itemId;
    private BigDecimal amount;
    private String orderState;

    // ===== 新增字段 =====
    private String deptName;
    private LocalDateTime visitDate;
    private LocalDateTime createTime;
    private LocalDateTime payTime;
}