package com.neuedu.his.service;

import com.neuedu.his.model.dto.MedicalTechExecuteRequestDTO;
import com.neuedu.his.model.dto.MedicalTechReportRequestDTO;
import com.neuedu.his.model.dto.MedicalTechTaskQueryDTO;
import com.neuedu.his.model.vo.MedicalTechInterpretationVO;
import com.neuedu.his.model.vo.MedicalTechTaskVO;
import com.neuedu.his.model.vo.PageResult;

public interface MedicalTechService {
    PageResult<MedicalTechTaskVO> getTasks(MedicalTechTaskQueryDTO query);
    void execute(String itemType, Integer itemId, MedicalTechExecuteRequestDTO request);
    void report(String itemType, Integer itemId, MedicalTechReportRequestDTO request);
    MedicalTechInterpretationVO aiInterpret(String itemType, Integer itemId);
}
