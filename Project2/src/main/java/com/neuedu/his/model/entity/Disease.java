package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class Disease {
    private Integer id;
    private String diseaseCode;
    private String diseaseName;
    private String diseaseICD;
    private String diseaseCategory;
    private LocalDateTime createTime;
    private LocalDateTime updateTime;
}