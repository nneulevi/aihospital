package com.neuedu.his.model.vo;

import lombok.Data;

@Data
public class DeptStatsVO {
    private Integer id;
    private String name;
    private String icon;
    private Integer doctorCount;
    private Integer visits;
    private Double revisitRate;
    private Double avgRating;
    private String status;
    private Integer saturation;
}