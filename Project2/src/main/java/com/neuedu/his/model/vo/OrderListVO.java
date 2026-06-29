package com.neuedu.his.model.vo;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class OrderListVO {
    private Integer registerId;
    private String itemType;
    private String itemName;
    private Integer itemId;
    private BigDecimal amount;
    private String orderState;
}