package com.neuedu.his.service.impl;

import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.vo.ConsultationResponseVO;
import com.neuedu.his.service.ConsultationService;
import org.springframework.stereotype.Service;

@Service
public class ConsultationServiceRealImpl implements ConsultationService {

    @Override
    public ConsultationResponseVO triage(ConsultationRequestDTO request) {
        // TODO: 接入真实AI模型（百度灵医、讯飞医疗等）
        throw new UnsupportedOperationException("真实AI模型待接入");
    }
}