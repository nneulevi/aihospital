package com.neuedu.his.model.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.Data;

import java.util.List;

@Data
public class InspectionRequestCreateDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotEmpty(message = "检验项目不能为空")
    @Valid
    private List<InspectionItemDTO> items;

    @Data
    public static class InspectionItemDTO {
        @NotNull(message = "医技项目ID不能为空")
        private Integer medicalTechnologyId;

        @NotBlank(message = "检验项目名称不能为空")
        private String inspectionInfo;
        @NotBlank(message = "检验样本不能为空")
        private String inspectionPosition;
    }
}
