package com.neuedu.his.model.vo;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class CheckResultDetailVO {
    private Integer id;
    private Integer registerId;
    private String itemType;
    private String itemName;
    private String itemPosition;
    private String result;
    private String state;
    private String stateName;
    private LocalDateTime reportTime;
}
