package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiDiagnosisSuggestionMapper;
import com.neuedu.his.mapper.DiseaseMapper;
import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.entity.AiDiagnosisSuggestion;
import com.neuedu.his.model.entity.Disease;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.DiagnosisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
@Service
@Primary
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
            suggestions.add(createSuggestion(disease2, 0.72, "需排除"));
        }

        for (DiagnosisSuggestResponseVO.Suggestion s : suggestions) {
            AiDiagnosisSuggestion suggestion = new AiDiagnosisSuggestion();
            suggestion.setMedicalRecordId(request.getMedicalRecordId());
            suggestion.setAiDiagnosis(s.getDiseaseName());
            suggestion.setDiseaseId(Integer.parseInt(s.getDiseaseCode()));
            suggestion.setConfidence(BigDecimal.valueOf(s.getConfidence()));
            suggestion.setEvidenceBasis(s.getEvidence());
            suggestion.setAiModelVersion("Mock-v1.0");
            aiDiagnosisSuggestionMapper.insert(suggestion);
        }

        DiagnosisSuggestResponseVO response = new DiagnosisSuggestResponseVO();
        response.setSuggestions(suggestions);
        return response;
    }

    private DiagnosisSuggestResponseVO.Suggestion createSuggestion(Disease disease, Double confidence, String evidence) {
        DiagnosisSuggestResponseVO.Suggestion s = new DiagnosisSuggestResponseVO.Suggestion();
        s.setDiseaseName(disease.getDiseaseName());
        s.setDiseaseCode(disease.getId().toString());
        s.setConfidence(confidence);
        s.setEvidence(evidence);
        return s;
    }
}