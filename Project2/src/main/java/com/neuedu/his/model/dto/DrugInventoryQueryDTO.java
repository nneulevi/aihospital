package com.neuedu.his.model.dto;

import lombok.Data;

@Data
public class DrugInventoryQueryDTO extends PageQueryDTO {
    private String drugName;
    private String drugType;
    private Integer stockAlert; // 1-仅显示库存预警
}