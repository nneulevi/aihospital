package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DoctorStatsVO {
    private Integer id;
    private String name;
    private String dept;
    private String title;
    private Integer visits;
    private Double revisitRate;
}