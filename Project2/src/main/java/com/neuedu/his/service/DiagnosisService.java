package com.neuedu.his.service;

import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;

public interface DiagnosisService {
    DiagnosisSuggestResponseVO suggest(DiagnosisSuggestRequestDTO request);
}