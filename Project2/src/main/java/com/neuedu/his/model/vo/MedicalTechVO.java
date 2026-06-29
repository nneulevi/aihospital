package com.neuedu.his.model.vo;

import lombok.Data;
import java.math.BigDecimal;

/**
 * 检验/检查项目VO
 */
@Data
public class MedicalTechVO {
    private Integer id;
    private String name;
    private String type;        // 大类: radiology/ultrasound/endoscopy/ecg/other
    private String typeName;    // 显示名称: 放射科/超声科/...
    private String bodyPart;    // 检查部位
    private BigDecimal price;
    private String tips;
}