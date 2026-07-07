package com.neuedu.his.service.impl;

import com.neuedu.his.client.HeadCtClinicalAssistClient;
import com.neuedu.his.mapper.AiConsultationMapper;
import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.entity.AiConsultation;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ConsultationService;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

public class ConsultationServiceRealImpl implements ConsultationService {

    @Autowired
    private HeadCtClinicalAssistClient clinicalAssistClient;

    @Autowired
    private AiConsultationMapper aiConsultationMapper;

    @Override
    public ConsultationResponseVO triage(ConsultationRequestDTO request) {
        Map<String, Object> body = new LinkedHashMap<>();
        if (request.getPatientId() != null) {
            body.put("patient_id", request.getPatientId());
        }
        body.put("symptoms", request.getSymptoms());
        body.put("conversation_id", consultationConversationId(request));
        body.put("user_id", consultationUserId(request));
        body.put("role_scope", request.getPatientId() == null ? "doctor" : "patient");
        body.put("memory_enabled", true);

        Map<String, Object> assist = clinicalAssistClient.consultation(body);
        List<ConsultationResponseVO.DeptRecommendation> recommendations = parseRecommendations(assist.get("recommendations"));
        String diagnosisHint = Objects.toString(assist.get("diagnosis_hint"), "AI辅助问诊结果仅供医生参考，最终结论需医生审核。");

        if (request.getPatientId() == null) {
            ConsultationResponseVO response = new ConsultationResponseVO();
            response.setDiagnosisHint(diagnosisHint);
            response.setRecommendations(recommendations);
            return response;
        }

        AiConsultation consultation = new AiConsultation();
        consultation.setPatientId(request.getPatientId());
        consultation.setSymptomsDesc(request.getSymptoms());
        consultation.setAiRecommendDept(JsonUtil.toJson(assist));
        consultation.setAiDiagnosisHint(diagnosisHint);
        consultation.setAiModelVersion(modelVersion(assist));
        aiConsultationMapper.insert(consultation);

        ConsultationResponseVO response = new ConsultationResponseVO();
        response.setConsultationId(consultation.getId());
        response.setDiagnosisHint(diagnosisHint);
        response.setRecommendations(recommendations);
        return response;
    }

    private String consultationConversationId(ConsultationRequestDTO request) {
        if (request.getConversationId() != null && !request.getConversationId().isBlank()) {
            return request.getConversationId();
        }
        if (request.getPatientId() != null) {
            return "patient:" + request.getPatientId() + ":consultation";
        }
        return "doctor-triage:" + UUID.randomUUID();
    }

    private String consultationUserId(ConsultationRequestDTO request) {
        if (request.getPatientId() != null) {
            return "patient:" + request.getPatientId();
        }
        return "doctor";
    }

    private List<ConsultationResponseVO.DeptRecommendation> parseRecommendations(Object value) {
        List<ConsultationResponseVO.DeptRecommendation> output = new ArrayList<>();
        if (!(value instanceof List<?> items)) {
            return output;
        }
        for (Object item : items) {
            if (!(item instanceof Map<?, ?> map)) {
                continue;
            }
            ConsultationResponseVO.DeptRecommendation recommendation = new ConsultationResponseVO.DeptRecommendation();
            recommendation.setDeptId(toInteger(first(map, "dept_id", "deptId")));
            recommendation.setDeptName(Objects.toString(first(map, "dept_name", "deptName"), ""));
            recommendation.setConfidence(toDouble(map.get("confidence")));
            recommendation.setReason(Objects.toString(map.get("reason"), ""));
            output.add(recommendation);
        }
        return output;
    }

    private Object first(Map<?, ?> map, String... names) {
        for (String name : names) {
            if (map.containsKey(name)) {
                return map.get(name);
            }
        }
        return null;
    }

    private Integer toInteger(Object value) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value == null) {
            return null;
        }
        try {
            return Integer.parseInt(value.toString());
        } catch (NumberFormatException ignored) {
            return null;
        }
    }

    private Double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value == null) {
            return 0.0;
        }
        try {
            return Double.parseDouble(value.toString());
        } catch (NumberFormatException ignored) {
            return 0.0;
        }
    }

    @SuppressWarnings("unchecked")
    private String modelVersion(Map<String, Object> assist) {
        Object llm = assist.get("llm_context");
        if (llm instanceof Map<?, ?> map) {
            Object model = ((Map<String, Object>) map).get("model");
            if (model != null) {
                return "RAG+LLM:" + model;
            }
        }
        return "RAG+LLM";
    }
}
