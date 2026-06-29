package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.mapper.AiScheduleResultMapper;
import com.neuedu.his.mapper.AiScheduleRuleMapper;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.model.dto.ScheduleGenerateRequestDTO;
import com.neuedu.his.model.dto.ScheduleResultQueryDTO;
import com.neuedu.his.model.entity.AiScheduleResult;
import com.neuedu.his.model.entity.AiScheduleRule;
import com.neuedu.his.model.entity.Employee;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.ScheduleGenerateResponseVO;
import com.neuedu.his.model.vo.ScheduleResultVO;
import com.neuedu.his.service.ScheduleService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

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
}