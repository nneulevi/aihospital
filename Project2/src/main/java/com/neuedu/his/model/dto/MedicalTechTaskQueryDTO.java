package com.neuedu.his.model.dto;

import lombok.Data;

@Data
public class MedicalTechTaskQueryDTO {
    private Integer registerId;
    private String itemType;
    private String state;
    private Integer pageNum = 1;
    private Integer pageSize = 10;
}
