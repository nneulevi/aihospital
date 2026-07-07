package com.neuedu.his.service;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.neuedu.his.client.HeadCtClinicalAssistClient;
import com.neuedu.his.mapper.AiConsultationMapper;
import com.neuedu.his.mapper.AiDiagnosisSuggestionMapper;
import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.entity.AiConsultation;
import com.neuedu.his.model.entity.AiDiagnosisSuggestion;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.util.JsonUtil;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.io.OutputStream;
import java.math.BigDecimal;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

@Service
public class ClinicalAiStreamService {
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final HeadCtClinicalAssistClient clinicalAssistClient;
    private final AiConsultationMapper aiConsultationMapper;
    private final AiDiagnosisSuggestionMapper aiDiagnosisSuggestionMapper;
    private final ObjectMapper objectMapper = new ObjectMapper();

    public ClinicalAiStreamService(
            HeadCtClinicalAssistClient clinicalAssistClient,
            AiConsultationMapper aiConsultationMapper,
            AiDiagnosisSuggestionMapper aiDiagnosisSuggestionMapper
    ) {
        this.clinicalAssistClient = clinicalAssistClient;
        this.aiConsultationMapper = aiConsultationMapper;
        this.aiDiagnosisSuggestionMapper = aiDiagnosisSuggestionMapper;
    }

    public void streamConsultation(ConsultationRequestDTO request, OutputStream outputStream) throws IOException {
        Map<String, Object> body = new LinkedHashMap<>();
        if (request.getPatientId() != null) {
            body.put("patient_id", request.getPatientId());
        }
        body.put("symptoms", request.getSymptoms());
        body.put("conversation_id", consultationConversationId(request));
        body.put("user_id", consultationUserId(request));
        body.put("role_scope", request.getPatientId() == null ? "doctor" : "patient");
        body.put("memory_enabled", true);

        clinicalAssistClient.streamConsultation(body, (event, data) -> {
            if ("final".equals(event)) {
                Map<String, Object> payload = parseMap(data);
                Map<String, Object> assist = asMap(payload.get("result"));
                ConsultationResponseVO response = persistConsultation(request, assist);
                writeEvent(outputStream, "final", Map.of("status", "success", "data", response));
            } else {
                writeRawEvent(outputStream, event, data);
            }
        });
    }

    public void streamDiagnosis(DiagnosisSuggestRequestDTO request, OutputStream outputStream) throws IOException {
        Map<String, Object> body = new LinkedHashMap<>();
        if (request.getMedicalRecordId() != null) {
            body.put("medical_record_id", request.getMedicalRecordId());
        }
        body.put("symptoms", request.getSymptoms());
        body.put("history", request.getHistory());
        body.put("physique", request.getPhysique());
        body.put("conversation_id", diagnosisConversationId(request));
        body.put("user_id", "doctor");
        body.put("role_scope", "doctor");
        body.put("memory_enabled", true);

        clinicalAssistClient.streamDiagnosis(body, (event, data) -> {
            if ("final".equals(event)) {
                Map<String, Object> payload = parseMap(data);
                Map<String, Object> assist = asMap(payload.get("result"));
                DiagnosisSuggestResponseVO response = persistDiagnosis(request, assist);
                writeEvent(outputStream, "final", Map.of("status", "success", "data", response));
            } else {
                writeRawEvent(outputStream, event, data);
            }
        });
    }

    private ConsultationResponseVO persistConsultation(ConsultationRequestDTO request, Map<String, Object> assist) {
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

    private DiagnosisSuggestResponseVO persistDiagnosis(DiagnosisSuggestRequestDTO request, Map<String, Object> assist) {
        List<DiagnosisSuggestResponseVO.Suggestion> suggestions = parseSuggestions(assist.get("suggestions"));
        String modelVersion = modelVersion(assist);
        if (request.getMedicalRecordId() == null) {
            DiagnosisSuggestResponseVO response = new DiagnosisSuggestResponseVO();
            response.setSuggestions(suggestions);
            return response;
        }
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

    private String diagnosisConversationId(DiagnosisSuggestRequestDTO request) {
        if (request.getConversationId() != null && !request.getConversationId().isBlank()) {
            return request.getConversationId();
        }
        if (request.getMedicalRecordId() != null) {
            return "medical_record:" + request.getMedicalRecordId() + ":diagnosis";
        }
        return "standalone-diagnosis:" + UUID.randomUUID();
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

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return new LinkedHashMap<>();
    }

    private Map<String, Object> parseMap(String data) {
        try {
            return objectMapper.readValue(data, MAP_TYPE);
        } catch (JsonProcessingException ex) {
            throw new IllegalStateException("Failed to parse clinical stream event", ex);
        }
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

    private void writeEvent(OutputStream outputStream, String event, Object payload) throws IOException {
        writeRawEvent(outputStream, event, JsonUtil.toJson(payload));
    }

    private void writeRawEvent(OutputStream outputStream, String event, String jsonData) throws IOException {
        outputStream.write(("event: " + event + "\n").getBytes(StandardCharsets.UTF_8));
        outputStream.write(("data: " + jsonData + "\n\n").getBytes(StandardCharsets.UTF_8));
        outputStream.flush();
    }
}
