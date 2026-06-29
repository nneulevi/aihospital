package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.mapper.AiScheduleResultMapper;
import com.neuedu.his.mapper.AiScheduleRuleMapper;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.mapper.SchedulingMapper;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.AiScheduleResult;
import com.neuedu.his.model.entity.AiScheduleRule;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.entity.Scheduling;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleGenerateResponseVO;
import com.neuedu.his.model.vo.ScheduleResultVO;
import com.neuedu.his.model.vo.ScheduleSourceVO;
import com.neuedu.his.service.ScheduleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

@Service
public class ScheduleServiceImpl implements ScheduleService {

    @Autowired
    private AiScheduleResultMapper aiScheduleResultMapper;

    @Autowired
    private AiScheduleRuleMapper aiScheduleRuleMapper;

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private SchedulingMapper schedulingMapper;

    @Override
    public ScheduleGenerateResponseVO generate(ScheduleGenerateRequestDTO request) {
        List<AiScheduleRule> rules = aiScheduleRuleMapper.selectActiveByDept(request.getDeptId());

        List<Employee> doctors = employeeMapper.selectByRole("DOCTOR", request.getDeptId());
        List<AiScheduleResult> results = new ArrayList<>();

        LocalDate current = request.getStartDate();
        LocalDate end = request.getEndDate();

        while (!current.isAfter(end)) {
            for (int i = 0; i < Math.min(3, doctors.size()); i++) {
                AiScheduleResult result = new AiScheduleResult();
                result.setEmployeeId(doctors.get(i).getId());
                result.setDeptmentId(request.getDeptId());
                result.setScheduleDate(current);
                result.setShiftType("MORNING");
                result.setRegistQuota(20);
                result.setIsGenerated((short) 1);
                result.setIsModified((short) 0);
                result.setSourceType("AI");
                results.add(result);
            }
            for (int i = 0; i < Math.min(3, doctors.size()); i++) {
                AiScheduleResult result = new AiScheduleResult();
                result.setEmployeeId(doctors.get(i).getId());
                result.setDeptmentId(request.getDeptId());
                result.setScheduleDate(current);
                result.setShiftType("AFTERNOON");
                result.setRegistQuota(20);
                result.setIsGenerated((short) 1);
                result.setIsModified((short) 0);
                result.setSourceType("AI");
                results.add(result);
            }
            current = current.plusDays(1);
        }

        for (AiScheduleResult result : results) {
            aiScheduleResultMapper.insert(result);
        }

        ScheduleGenerateResponseVO response = new ScheduleGenerateResponseVO();
        List<ScheduleGenerateResponseVO.DailySchedule> dailySchedules = new ArrayList<>();
        response.setResults(dailySchedules);
        return response;
    }

    @Override
    public PageResult<ScheduleResultVO> getResults(ScheduleResultQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<AiScheduleResult> list = aiScheduleResultMapper.selectByDateRange(
                query.getDeptId(), query.getStartDate(), query.getEndDate());
        PageInfo<AiScheduleResult> pageInfo = new PageInfo<>(list);

        List<ScheduleResultVO> voList = new ArrayList<>();
        for (AiScheduleResult r : list) {
            ScheduleResultVO vo = new ScheduleResultVO();
            vo.setDoctorId(r.getEmployeeId());
            vo.setScheduleDate(r.getScheduleDate());
            vo.setShiftType(r.getShiftType());
            Employee emp = employeeMapper.selectById(r.getEmployeeId());
            if (emp != null) {
                vo.setDoctorName(emp.getRealname());
            }
            voList.add(vo);
        }

        PageResult<ScheduleResultVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    @Override
    public PageResult<ScheduleSourceVO> getSources(ScheduleSourceQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<ScheduleSourceVO> list = schedulingMapper.selectSources(
                query.getDeptId(), query.getDoctorId(), query.getStartDate(), query.getEndDate());
        PageInfo<ScheduleSourceVO> pageInfo = new PageInfo<>(list);
        PageResult<ScheduleSourceVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(list);
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Integer createSource(ScheduleSourceCreateDTO request) {
        Employee doctor = employeeMapper.selectById(request.getDoctorId());
        if (doctor == null || !"DOCTOR".equals(doctor.getRoleType())) {
            throw new BusinessException("排班医生不存在或角色不正确");
        }
        Scheduling scheduling = new Scheduling();
        scheduling.setEmployeeId(request.getDoctorId());
        scheduling.setDeptmentId(request.getDeptId());
        scheduling.setScheduleDate(request.getScheduleDate());
        scheduling.setNoon(request.getNoon());
        scheduling.setRegistQuota(request.getRegistQuota());
        scheduling.setScheduleStatus("NORMAL");
        scheduling.setSourceType(request.getSourceType() == null ? "MANUAL" : request.getSourceType());
        schedulingMapper.insert(scheduling);
        return scheduling.getId();
    }

    @Override
    public void updateQuota(Integer scheduleId, ScheduleQuotaUpdateDTO request) {
        requireSchedule(scheduleId);
        schedulingMapper.updateQuota(scheduleId, request.getRegistQuota());
    }

    @Override
    public void suspend(Integer scheduleId) {
        requireSchedule(scheduleId);
        schedulingMapper.updateStatus(scheduleId, "SUSPENDED");
    }

    @Override
    public void resume(Integer scheduleId) {
        requireSchedule(scheduleId);
        schedulingMapper.updateStatus(scheduleId, "NORMAL");
    }

    private Scheduling requireSchedule(Integer scheduleId) {
        Scheduling scheduling = schedulingMapper.selectById(scheduleId);
        if (scheduling == null) {
            throw new BusinessException("号源不存在");
        }
        return scheduling;
    }
}
