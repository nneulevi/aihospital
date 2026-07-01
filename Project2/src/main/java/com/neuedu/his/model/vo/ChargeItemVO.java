package com.neuedu.his.model.vo;

import com.neuedu.his.model.entity.ChargeItem;
import lombok.Data;
import lombok.EqualsAndHashCode;

@Data
@EqualsAndHashCode(callSuper = true)
public class ChargeItemVO extends ChargeItem {
    private String patientName;
    private String operatorName;
    private String financeRecordNo;
}
