package com.neuedu.his.service;

import com.neuedu.his.model.dto.ReportGenerateRequestDTO;
import com.neuedu.his.model.vo.ReportGenerateResponseVO;

public interface ReportService {
    ReportGenerateResponseVO generate(ReportGenerateRequestDTO request);
}