package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class MedicalRecord {
    private Integer id;
    private Integer registerId;
    private Integer doctorId;
    private String readme;
    private String present;
    private String presentTreat;
    private String history;
    private String allergy;
    private String physique;
    private String proposal;
    private String careful;
    private String diagnosis;
    private String cure;
    private String recordStatus;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}