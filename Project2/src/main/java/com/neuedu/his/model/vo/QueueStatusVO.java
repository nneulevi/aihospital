package com.neuedu.his.model.vo;

import lombok.Data;
import java.util.List;

/**
 * 候诊状态VO
 */
@Data
public class QueueStatusVO {
    private String queueNumber;
    private Integer aheadCount;
    private String currentCalling;
    private String currentRoom;
    private String deptName;
    private List<QueueItemVO> queueList;
}