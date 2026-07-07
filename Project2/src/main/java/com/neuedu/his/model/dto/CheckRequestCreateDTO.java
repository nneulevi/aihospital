package com.neuedu.his.model.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
public class CheckRequestCreateDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotEmpty(message = "检查项目不能为空")
    @Valid
    private List<CheckItemDTO> items;

    @Data
    public static class CheckItemDTO {
        @NotNull(message = "医技项目ID不能为空")
        private Integer medicalTechnologyId;

        @NotBlank(message = "检查项目名称不能为空")
        private String checkInfo;
        @NotBlank(message = "检查部位不能为空")
        private String checkPosition;
    }
}
