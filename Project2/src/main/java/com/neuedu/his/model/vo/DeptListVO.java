package com.neuedu.his.model.vo;

import lombok.Data;

/**
 * 科室列表VO（患者端）
 */
@Data
public class DeptListVO {
    private Integer id;
    private String name;
    private String icon;
    private String description;

    /**
     * 根据科室名称生成图标和描述
     */
    public static DeptListVO fromDepartment(Integer id, String name) {
        DeptListVO vo = new DeptListVO();
        vo.setId(id);
        vo.setName(name);
        vo.setIcon(getIconByName(name));
        vo.setDescription(getDescriptionByName(name));
        return vo;
    }

    private static String getIconByName(String name) {
        if (name == null) return "🏥";
        if (name.contains("神经")) return "🧠";
        if (name.contains("呼吸")) return "🫁";
        if (name.contains("消化")) return "🫀";
        if (name.contains("心血管") || name.contains("心脏") || name.contains("心内")) return "❤️";
        if (name.contains("骨科") || name.contains("骨伤")) return "🦴";
        if (name.contains("儿科") || name.contains("小儿")) return "👶";
        if (name.contains("眼科") || name.contains("眼")) return "👁️";
        if (name.contains("皮肤") || name.contains("皮")) return "🧴";
        if (name.contains("耳鼻喉") || name.contains("耳")) return "👂";
        if (name.contains("口腔") || name.contains("牙")) return "🦷";
        if (name.contains("妇科") || name.contains("产科") || name.contains("妇产")) return "👩‍⚕️";
        if (name.contains("泌尿")) return "🫘";
        if (name.contains("普外") || name.contains("外科")) return "🔬";
        if (name.contains("康复") || name.contains("理疗")) return "💪";
        if (name.contains("中医")) return "🌿";
        if (name.contains("急诊")) return "🚨";
        return "🏥";
    }

    private static String getDescriptionByName(String name) {
        if (name == null) return "点击查看医生排班";
        if (name.contains("神经")) return "脑血管疾病、头痛头晕、癫痫";
        if (name.contains("呼吸")) return "感冒、咳嗽、肺炎、哮喘";
        if (name.contains("消化")) return "胃痛、腹泻、消化不良";
        if (name.contains("心血管")) return "高血压、冠心病、心律失常";
        if (name.contains("骨科")) return "骨折、关节痛、腰椎间盘突出";
        if (name.contains("儿科")) return "儿童常见病、生长发育";
        if (name.contains("眼科")) return "近视、白内障、眼底病";
        if (name.contains("皮肤")) return "湿疹、痤疮、过敏";
        if (name.contains("耳鼻喉")) return "鼻炎、咽炎、中耳炎";
        if (name.contains("口腔")) return "牙痛、牙周病、正畸";
        if (name.contains("妇产")) return "妇科疾病、孕产保健";
        if (name.contains("泌尿")) return "泌尿系统疾病";
        if (name.contains("普外") || name.contains("外科")) return "外科疾病诊治";
        if (name.contains("康复")) return "康复理疗、功能训练";
        if (name.contains("中医")) return "中医调理、针灸推拿";
        if (name.contains("急诊")) return "紧急救治、绿色通道";
        return "点击查看医生排班";
    }
}