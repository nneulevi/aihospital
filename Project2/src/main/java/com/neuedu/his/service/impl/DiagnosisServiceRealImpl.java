package com.neuedu.his.service.impl;

import com.neuedu.his.client.HeadCtClinicalAssistClient;
import com.neuedu.his.mapper.AiDiagnosisSuggestionMapper;
import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.entity.AiDiagnosisSuggestion;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.DiagnosisService;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class DiagnosisServiceRealImpl implements DiagnosisService {

    @Autowired
    private HeadCtClinicalAssistClient clinicalAssistClient;

    @Autowired
    private AiDiagnosisSuggestionMapper aiDiagnosisSuggestionMapper;

    @Override
    public DiagnosisSuggestResponseVO suggest(DiagnosisSuggestRequestDTO request) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("medical_record_id", request.getMedicalRecordId());
        body.put("symptoms", request.getSymptoms());
        body.put("history", request.getHistory());
        body.put("physique", request.getPhysique());
        body.put("conversation_id", "medical_record:" + request.getMedicalRecordId() + ":diagnosis");
        body.put("user_id", "doctor");
        body.put("role_scope", "doctor");
        body.put("memory_enabled", true);

        Map<String, Object> assist = clinicalAssistClient.diagnosis(body);
        List<DiagnosisSuggestResponseVO.Suggestion> suggestions = parseSuggestions(assist.get("suggestions"));
        String modelVersion = modelVersion(assist);

        for (DiagnosisSuggestResponseVO.Suggestion item : suggestions) {
            AiDiagnosisSuggestion entity = new AiDiagnosisSuggestion();
            entity.setMedicalRecordId(request.getMedicalRecordId());
            entity.setAiDiagnosis(item.getDiseaseName());
            entity.setDiseaseId(parseDiseaseId(item.getDiseaseCode()));
            entity.setConfidence(BigDecimal.valueOf(item.getConfidence() == null ? 0.0 : item.getConfidence()));
            Map<String, Object> evidence = new LinkedHashMap<>();
            evidence.put("evidence", item.getEvidence());
            evidence.put("rag_context", assist.get("rag_context"));
            evidence.put("llm_context", assist.get("llm_context"));
            evidence.put("memory_context", assist.get("memory_context"));
            evidence.put("task_id", assist.get("task_id"));
            entity.setEvidenceBasis(JsonUtil.toJson(evidence));
            entity.setAiModelVersion(modelVersion);
            aiDiagnosisSuggestionMapper.insert(entity);
        }

        DiagnosisSuggestResponseVO response = new DiagnosisSuggestResponseVO();
        response.setSuggestions(suggestions);
        return response;
    }

    private List<DiagnosisSuggestResponseVO.Suggestion> parseSuggestions(Object value) {
        List<DiagnosisSuggestResponseVO.Suggestion> output = new ArrayList<>();
        if (!(value instanceof List<?> items)) {
            return output;
        }
        for (Object item : items) {
            if (!(item instanceof Map<?, ?> map)) {
                continue;
            }
            DiagnosisSuggestResponseVO.Suggestion suggestion = new DiagnosisSuggestResponseVO.Suggestion();
            suggestion.setDiseaseName(Objects.toString(first(map, "disease_name", "diseaseName"), ""));
            suggestion.setDiseaseCode(Objects.toString(first(map, "disease_code", "diseaseCode", "disease_id", "diseaseId"), ""));
            suggestion.setConfidence(toDouble(map.get("confidence")));
            suggestion.setEvidence(Objects.toString(map.get("evidence"), ""));
            output.add(suggestion);
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

    private Integer parseDiseaseId(String value) {
        if (value == null || value.isBlank()) {
            return null;
        }
        try {
            return Integer.parseInt(value);
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
