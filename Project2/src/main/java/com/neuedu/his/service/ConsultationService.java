package com.neuedu.his.service;

import com.neuedu.his.model.dto.ConsultationRequestDTO;
import com.neuedu.his.model.vo.ConsultationResponseVO;

public interface ConsultationService {
    ConsultationResponseVO triage(ConsultationRequestDTO request);
}