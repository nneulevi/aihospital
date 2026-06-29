package com.neuedu.his.service;

import com.neuedu.his.model.dto.ScheduleGenerateRequestDTO;
import com.neuedu.his.model.dto.ScheduleQuotaUpdateDTO;
import com.neuedu.his.model.dto.ScheduleResultQueryDTO;
import com.neuedu.his.model.dto.ScheduleSourceCreateDTO;
import com.neuedu.his.model.dto.ScheduleSourceQueryDTO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleGenerateResponseVO;
import com.neuedu.his.model.vo.ScheduleResultVO;
import com.neuedu.his.model.vo.ScheduleSourceVO;

public interface ScheduleService {
    ScheduleGenerateResponseVO generate(ScheduleGenerateRequestDTO request);
    PageResult<ScheduleResultVO> getResults(ScheduleResultQueryDTO query);
    PageResult<ScheduleSourceVO> getSources(ScheduleSourceQueryDTO query);
    Integer createSource(ScheduleSourceCreateDTO request);
    void updateQuota(Integer scheduleId, ScheduleQuotaUpdateDTO request);
    void suspend(Integer scheduleId);
    void resume(Integer scheduleId);
}
