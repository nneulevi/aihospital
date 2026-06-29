package com.neuedu.his.model.dto;

import jakarta.validation.constraints.*;
import lombok.Data;

import java.util.List;

@Data
public class PrescriptionCreateDTO {
    @NotNull(message = "挂号ID不能为空")
    private Integer registerId;

    @NotNull(message = "医生ID不能为空")
    private Integer doctorId;

    @NotEmpty(message = "处方药品不能为空")
    private List<PrescriptionItemDTO> items;

    @Data
    public static class PrescriptionItemDTO {
        @NotNull(message = "药品ID不能为空")
        private Integer drugId;

        @NotBlank(message = "用法不能为空")
        private String usageRoute;

        @NotBlank(message = "频次不能为空")
        private String frequency;

        @NotBlank(message = "单次用量不能为空")
        private String dosage;

        private String singleDose;

        @Min(value = 1, message = "用药天数至少1天")
        @Max(value = 90, message = "用药天数不超过90天")
        private Integer useDays;

        @Min(value = 1, message = "药品数量至少1")
        @Max(value = 999, message = "药品数量不超过999")
        private Integer drugNumber;
    }
}