package com.neuedu.his.model.entity;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AiImageFile {
    private Integer id;
    private Integer checkRequestId;
    private Integer registerId;
    private String filePath;
    private String fileName;
    private Long fileSize;
    private String fileFormat;
    private LocalDateTime uploadTime;
    private Integer uploadBy;
    private LocalDateTime createTime;
}