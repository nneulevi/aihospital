package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiDiagnosisSuggestionMapper;
import com.neuedu.his.mapper.DiseaseMapper;
import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.entity.AiDiagnosisSuggestion;
import com.neuedu.his.model.entity.Disease;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.DiagnosisService;
import org.springframework.beans.factory.annotation.Autowired;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

public class DiagnosisServiceMockImpl implements DiagnosisService {

    @Autowired
    private AiDiagnosisSuggestionMapper aiDiagnosisSuggestionMapper;

    @Autowired
    private DiseaseMapper diseaseMapper;

    @Override
    public DiagnosisSuggestResponseVO suggest(DiagnosisSuggestRequestDTO request) {
        List<DiagnosisSuggestResponseVO.Suggestion> suggestions = new ArrayList<>();

        Disease disease1 = diseaseMapper.selectById(1);
        if (disease1 != null) {
            suggestions.add(createSuggestion(disease1, 0.85, "症状描述符合"));
        }

        Disease disease2 = diseaseMapper.selectById(2);
        if (disease2 != null) {
            suggestions.add(createSuggestion(disease2, 0.72, "需结合检查结果排除"));
        }

        for (DiagnosisSuggestResponseVO.Suggestion item : suggestions) {
            AiDiagnosisSuggestion suggestion = new AiDiagnosisSuggestion();
            suggestion.setMedicalRecordId(request.getMedicalRecordId());
            suggestion.setAiDiagnosis(item.getDiseaseName());
            suggestion.setDiseaseId(Integer.parseInt(item.getDiseaseCode()));
            suggestion.setConfidence(BigDecimal.valueOf(item.getConfidence()));
            suggestion.setEvidenceBasis(item.getEvidence());
            suggestion.setAiModelVersion("Mock-v1.0");
            aiDiagnosisSuggestionMapper.insert(suggestion);
        }

        DiagnosisSuggestResponseVO response = new DiagnosisSuggestResponseVO();
        response.setSuggestions(suggestions);
        return response;
    }

    private DiagnosisSuggestResponseVO.Suggestion createSuggestion(Disease disease, Double confidence, String evidence) {
        DiagnosisSuggestResponseVO.Suggestion suggestion = new DiagnosisSuggestResponseVO.Suggestion();
        suggestion.setDiseaseName(disease.getDiseaseName());
        suggestion.setDiseaseCode(disease.getId().toString());
        suggestion.setConfidence(confidence);
        suggestion.setEvidence(evidence);
        return suggestion;
    }
}
