package com.neuedu.his.service;

import com.neuedu.his.model.dto.ScheduleGenerateRequestDTO;
import com.neuedu.his.model.dto.ScheduleResultQueryDTO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleGenerateResponseVO;
import com.neuedu.his.model.vo.ScheduleResultVO;

public interface ScheduleService {
    ScheduleGenerateResponseVO generate(ScheduleGenerateRequestDTO request);
    PageResult<ScheduleResultVO> getResults(ScheduleResultQueryDTO query);
}