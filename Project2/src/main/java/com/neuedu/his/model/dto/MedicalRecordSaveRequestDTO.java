package com.neuedu.his.model.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class MedicalRecordSaveRequestDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @Size(max = 200, message = "主诉长度不超过200字")
    private String readme;

    @Size(max = 500, message = "现病史长度不超过500字")
    private String present;

    private String presentTreat;
    private String history;
    private String allergy;
    private String physique;

    @Size(max = 500, message = "检查建议长度不超过500字")
    private String proposal;

    private String careful;
    private String diagnosis;
}