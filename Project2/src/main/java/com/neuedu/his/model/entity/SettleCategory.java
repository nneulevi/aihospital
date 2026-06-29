package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class SettleCategory {
    private Integer id;
    private String settleCode;
    private String settleName;
    private Integer sequenceNo;
    private Boolean delmark;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}