package com.neuedu.his.model.vo;

import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.entity.DisposalRequest;
import com.neuedu.his.model.entity.InspectionRequest;
import lombok.Data;

import java.util.List;

@Data
public class CheckResultVO {
    private List<CheckRequest> checkRequests;
    private List<InspectionRequest> inspectionRequests;
    private List<DisposalRequest> disposalRequests;
}