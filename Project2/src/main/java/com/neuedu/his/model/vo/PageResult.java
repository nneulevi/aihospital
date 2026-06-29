package com.neuedu.his.model.vo;

import lombok.Data;

import java.util.List;

@Data
public class PageResult<T> {
    private Long total;
    private Integer pageNum;
    private Integer pageSize;
    private Integer totalPages;
    private List<T> records;
}