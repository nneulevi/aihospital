package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class MedicalTechInterpretationVO {
    private String itemType;
    private Integer itemId;
    private String summary;
    private String suggestion;
}
