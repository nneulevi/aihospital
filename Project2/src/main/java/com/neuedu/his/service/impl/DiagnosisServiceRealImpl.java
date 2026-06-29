package com.neuedu.his.service.impl;

import com.neuedu.his.model.dto.DiagnosisSuggestRequestDTO;
import com.neuedu.his.model.vo.DiagnosisSuggestResponseVO;
import com.neuedu.his.service.DiagnosisService;

public class DiagnosisServiceRealImpl implements DiagnosisService {

    @Override
    public DiagnosisSuggestResponseVO suggest(DiagnosisSuggestRequestDTO request) {
        throw new UnsupportedOperationException("真实AI模型待接入");
    }
}