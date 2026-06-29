package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiConsultationMapper;
import com.neuedu.his.mapper.DepartmentMapper;
import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.entity.AiConsultation;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ConsultationService;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
@Service          // ← 添加这个
@Primary          // ← 添加这个，让 Spring 默认使用 Moc
public class ConsultationServiceMockImpl implements ConsultationService {

    @Autowired
    private AiConsultationMapper aiConsultationMapper;

    @Autowired
    private DepartmentMapper departmentMapper;

    @Override
    public ConsultationResponseVO triage(ConsultationRequestDTO request) {
        String symptoms = request.getSymptoms();
        List<ConsultationResponseVO.DeptRecommendation> recommendations = new ArrayList<>();

        if (symptoms.contains("头") || symptoms.contains("晕") || symptoms.contains("痛")) {
            recommendations.add(createRec(1, "神经内科", 0.92));
            recommendations.add(createRec(2, "神经外科", 0.65));
        } else if (symptoms.contains("心") || symptoms.contains("胸") || symptoms.contains("闷")) {
            recommendations.add(createRec(3, "心内科", 0.88));
            recommendations.add(createRec(4, "呼吸科", 0.45));
        } else {
            recommendations.add(createRec(5, "内科", 0.70));
            recommendations.add(createRec(6, "全科", 0.60));
        }

        AiConsultation consultation = new AiConsultation();
        consultation.setPatientId(request.getPatientId());
        consultation.setSymptomsDesc(symptoms);
        consultation.setAiRecommendDept(JsonUtil.toJson(recommendations));
        consultation.setAiDiagnosisHint("建议进一步检查：" + symptoms.substring(0, Math.min(20, symptoms.length())));
        consultation.setAiModelVersion("Mock-v1.0");
        aiConsultationMapper.insert(consultation);

        ConsultationResponseVO response = new ConsultationResponseVO();
        response.setConsultationId(consultation.getId());
        response.setRecommendations(recommendations);
        return response;
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