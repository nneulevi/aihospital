package com.neuedu.his.model.dto;

import lombok.Data;

import java.util.List;

@Data
public class DiagnosisReceiveRequestDTO {
    private Integer registerId;
    private String diagnosis;
    private String cure;
    private List<Integer> diseaseIds;
}
