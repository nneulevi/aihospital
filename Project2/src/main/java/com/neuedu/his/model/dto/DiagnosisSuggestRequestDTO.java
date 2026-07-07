package com.neuedu.his.model.dto;

import lombok.Data;

@Data
public class DiagnosisSuggestRequestDTO {
    private Integer medicalRecordId;
    private String conversationId;

    private String symptoms;
    private String history;
    private String physique;
}
