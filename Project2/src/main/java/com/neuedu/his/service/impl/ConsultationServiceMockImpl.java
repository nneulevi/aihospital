package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiConsultationMapper;
import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.entity.AiConsultation;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ConsultationService;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.ArrayList;
import java.util.List;

public class ConsultationServiceMockImpl implements ConsultationService {

    @Autowired
    private AiConsultationMapper aiConsultationMapper;

    @Override
    public ConsultationResponseVO triage(ConsultationRequestDTO request) {
        String symptoms = request.getSymptoms() == null ? "" : request.getSymptoms();
        List<ConsultationResponseVO.DeptRecommendation> recommendations = new ArrayList<>();

        if (containsAny(symptoms, "头", "晕", "痛", "脑")) {
            recommendations.add(createRec(1, "神经内科", 0.92));
            recommendations.add(createRec(2, "神经外科", 0.65));
        } else if (containsAny(symptoms, "心", "胸", "闷")) {
            recommendations.add(createRec(3, "心内科", 0.88));
            recommendations.add(createRec(4, "呼吸科", 0.45));
        } else {
            recommendations.add(createRec(5, "内科", 0.70));
            recommendations.add(createRec(6, "全科", 0.60));
        }

        ConsultationResponseVO response = new ConsultationResponseVO();
        response.setDiagnosisHint("请结合症状持续时间、伴随体征、既往病史和必要检查综合判断；AI 分诊仅用于就诊科室建议。");
        response.setRecommendations(recommendations);
        if (request.getPatientId() != null) {
            AiConsultation consultation = new AiConsultation();
            consultation.setPatientId(request.getPatientId());
            consultation.setSymptomsDesc(symptoms);
            consultation.setAiRecommendDept(JsonUtil.toJson(recommendations));
            consultation.setAiDiagnosisHint("建议进一步检查: " + symptoms.substring(0, Math.min(20, symptoms.length())));
            consultation.setAiModelVersion("Mock-v1.0");
            aiConsultationMapper.insert(consultation);
            response.setConsultationId(consultation.getId());
        }
        return response;
    }

    private boolean containsAny(String text, String... words) {
        for (String word : words) {
            if (text.contains(word)) {
                return true;
            }
        }
        return false;
    }

    private ConsultationResponseVO.DeptRecommendation createRec(Integer deptId, String deptName, Double confidence) {
        ConsultationResponseVO.DeptRecommendation rec = new ConsultationResponseVO.DeptRecommendation();
        rec.setDeptId(deptId);
        rec.setDeptName(deptName);
        rec.setConfidence(confidence);
        rec.setReason("根据症状关键词匹配");
        return rec;
    }
}
