package com.neuedu.his.model.vo;

import lombok.Data;

/**
 * 候诊队列项VO
 */
@Data
public class QueueItemVO {
    private Integer registerId;
    private String patientName;
    private String deptName;
    private String doctorName;
    private String status;  // WAITING / PASSED
}