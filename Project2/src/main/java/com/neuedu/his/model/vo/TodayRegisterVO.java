package com.neuedu.his.model.vo;

import lombok.Data;
import java.time.LocalDate;

/**
 * 今日可报到VO
 */
@Data
public class TodayRegisterVO {
    private Integer registerId;
    private String deptName;
    private String doctorName;
    private LocalDate visitDate;
    private String noon;
    private String location;
    private String patientName;
    private Integer checkinStatus;
}