package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class CheckResultDetailVO {
    private Integer id;
    private String checkInfo;
    private String checkPosition;
    private String checkState;
    private String checkResult;
    private String checkRemark;
    private String createTime;
    private String checkTime;
    private String aiFindings;
    private String aiConclusion;
    private Double aiConfidence;
}