package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class QueueCountVO {
    private Integer patientId;
    private Integer registerId;
    private Integer queueCount;
    private String visitState;
    private String visitStateName;
}
