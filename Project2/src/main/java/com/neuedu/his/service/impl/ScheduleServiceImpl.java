package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.mapper.AiScheduleResultMapper;
import com.neuedu.his.mapper.AiScheduleRuleMapper;
import com.neuedu.his.mapper.EmployeeMapper;
import com.neuedu.his.mapper.RegisterMapper;
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
import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

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
    @Autowired
    private RegisterMapper registerMapper;

    @Override
    public ScheduleGenerateResponseVO generate(ScheduleGenerateRequestDTO request) {
        List<AiScheduleRule> rules = aiScheduleRuleMapper.selectActiveByDept(request.getDeptId());

        List<Employee> doctors = employeeMapper.selectByRole("DOCTOR", request.getDeptId());
        if (doctors.isEmpty()) {
            throw new BusinessException("当前科室暂无可排班医生，请先维护医生信息或选择其他科室");
        }
        List<AiScheduleResult> results = new ArrayList<>();

        LocalDate current = request.getStartDate();
        LocalDate end = request.getEndDate();
        if (end.isBefore(current)) {
            throw new BusinessException("排班结束日期不能早于开始日期");
        }

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

        Map<LocalDate, ScheduleGenerateResponseVO.DailySchedule> dailyMap = new LinkedHashMap<>();
        for (AiScheduleResult result : results) {
            aiScheduleResultMapper.insert(result);
            ScheduleGenerateResponseVO.DailySchedule daily = dailyMap.computeIfAbsent(
                    result.getScheduleDate(), scheduleDate -> {
                        ScheduleGenerateResponseVO.DailySchedule day = new ScheduleGenerateResponseVO.DailySchedule();
                        day.setDate(scheduleDate.toString());
                        day.setMorning(new ArrayList<>());
                        day.setAfternoon(new ArrayList<>());
                        return day;
                    });
            ScheduleGenerateResponseVO.DailySchedule.ShiftInfo shift = new ScheduleGenerateResponseVO.DailySchedule.ShiftInfo();
            shift.setEmployeeId(result.getEmployeeId());
            Employee employee = employeeMapper.selectById(result.getEmployeeId());
            shift.setEmployeeName(employee == null ? null : formatDoctorDisplayName(employee.getRealname()));
            shift.setQuota(result.getRegistQuota());
            shift.setShiftType(result.getShiftType());
            if ("AFTERNOON".equals(result.getShiftType())) {
                daily.getAfternoon().add(shift);
            } else {
                daily.getMorning().add(shift);
            }
            syncGeneratedScheduleToSource(result);
        }

        ScheduleGenerateResponseVO response = new ScheduleGenerateResponseVO();
        response.setScheduleRuleId(rules.isEmpty() ? null : rules.get(0).getId());
        response.setResults(new ArrayList<>(dailyMap.values()));
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
            vo.setId(r.getId());
            vo.setDeptId(r.getDeptmentId());
            vo.setDoctorId(r.getEmployeeId());
            vo.setScheduleDate(r.getScheduleDate());
            vo.setShiftType(r.getShiftType());
            vo.setRegistQuota(r.getRegistQuota());
            vo.setIsGenerated(r.getIsGenerated());
            vo.setIsModified(r.getIsModified());
            vo.setSourceType(r.getSourceType());
            Employee emp = employeeMapper.selectById(r.getEmployeeId());
            if (emp != null) {
                vo.setDoctorName(formatDoctorDisplayName(emp.getRealname()));
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
        return upsertScheduleSource(
                request.getDoctorId(),
                request.getDeptId(),
                request.getScheduleDate(),
                normalizeNoon(request.getNoon()),
                request.getRegistQuota(),
                request.getSourceType() == null ? "MANUAL" : request.getSourceType(),
                false
        ).getId();
    }

    @Override
    public void updateQuota(Integer scheduleId, ScheduleQuotaUpdateDTO request) {
        Scheduling scheduling = requireSchedule(scheduleId);
        requireQuotaNotBelowUsed(scheduling, request.getRegistQuota(), false);
        schedulingMapper.updateQuota(scheduleId, request.getRegistQuota());
    }

    @Override
    public void suspend(Integer scheduleId) {
        requireSchedule(scheduleId);
        schedulingMapper.updateStatus(scheduleId, "SUSPENDED");
    }

    @Override
    public void resume(Integer scheduleId) {
        Scheduling scheduling = requireSchedule(scheduleId);
        suspendDuplicateSchedules(scheduling);
        schedulingMapper.updateStatus(scheduleId, "NORMAL");
    }

    private Scheduling requireSchedule(Integer scheduleId) {
        Scheduling scheduling = schedulingMapper.selectById(scheduleId);
        if (scheduling == null) {
            throw new BusinessException("号源不存在");
        }
        return scheduling;
    }

    private void syncGeneratedScheduleToSource(AiScheduleResult result) {
        String noon = "AFTERNOON".equals(result.getShiftType()) ? "PM" : "AM";
        upsertScheduleSource(
                result.getEmployeeId(),
                result.getDeptmentId(),
                result.getScheduleDate(),
                noon,
                result.getRegistQuota(),
                "AI",
                true
        );
    }

    private Scheduling upsertScheduleSource(Integer doctorId, Integer deptId, LocalDate scheduleDate,
                                            String noon, Integer requestedQuota, String sourceType,
                                            boolean autoRaiseQuota) {
        if (requestedQuota == null || requestedQuota < 1) {
            throw new BusinessException("号源数量必须大于 0");
        }
        Integer effectiveQuota = effectiveQuota(doctorId, deptId, scheduleDate, noon, requestedQuota, autoRaiseQuota);
        List<Scheduling> existing = schedulingMapper.selectByCondition(deptId, doctorId, scheduleDate, scheduleDate);
        Scheduling matched = existing.stream()
                .filter(item -> noon.equals(normalizeNoon(item.getNoon())))
                .min(Comparator.comparing(item -> item.getId() == null ? Integer.MAX_VALUE : item.getId()))
                .orElse(null);
        if (matched == null) {
            Scheduling scheduling = new Scheduling();
            scheduling.setEmployeeId(doctorId);
            scheduling.setDeptmentId(deptId);
            scheduling.setScheduleDate(scheduleDate);
            scheduling.setNoon(noon);
            scheduling.setRegistQuota(effectiveQuota);
            scheduling.setScheduleStatus("NORMAL");
            scheduling.setSourceType(sourceType);
            schedulingMapper.insert(scheduling);
            return scheduling;
        }
        schedulingMapper.updateQuota(matched.getId(), effectiveQuota);
        schedulingMapper.updateStatus(matched.getId(), "NORMAL");
        matched.setRegistQuota(effectiveQuota);
        matched.setScheduleStatus("NORMAL");
        suspendDuplicateSchedules(matched);
        return matched;
    }

    private Integer effectiveQuota(Integer doctorId, Integer deptId, LocalDate scheduleDate, String noon,
                                   Integer requestedQuota, boolean autoRaiseQuota) {
        int used = registerMapper.countActiveBySchedule(deptId, doctorId, scheduleDate, noon);
        if (used > requestedQuota) {
            if (autoRaiseQuota) {
                return used;
            }
            throw new BusinessException("当前时段已有 " + used + " 个活跃预约，号源不能调整为 " + requestedQuota);
        }
        return requestedQuota;
    }

    private void requireQuotaNotBelowUsed(Scheduling scheduling, Integer requestedQuota, boolean autoRaiseQuota) {
        effectiveQuota(
                scheduling.getEmployeeId(),
                scheduling.getDeptmentId(),
                scheduling.getScheduleDate(),
                normalizeNoon(scheduling.getNoon()),
                requestedQuota,
                autoRaiseQuota
        );
    }

    private void suspendDuplicateSchedules(Scheduling keep) {
        List<Scheduling> sameSlot = schedulingMapper.selectByCondition(
                keep.getDeptmentId(),
                keep.getEmployeeId(),
                keep.getScheduleDate(),
                keep.getScheduleDate()
        );
        String noon = normalizeNoon(keep.getNoon());
        for (Scheduling item : sameSlot) {
            if (item.getId() != null
                    && !item.getId().equals(keep.getId())
                    && noon.equals(normalizeNoon(item.getNoon()))
                    && "NORMAL".equals(item.getScheduleStatus())) {
                schedulingMapper.updateStatus(item.getId(), "SUSPENDED");
            }
        }
    }

    private String normalizeNoon(String noon) {
        if ("MORNING".equalsIgnoreCase(noon)) {
            return "AM";
        }
        if ("AFTERNOON".equalsIgnoreCase(noon)) {
            return "PM";
        }
        return noon == null ? null : noon.trim().toUpperCase();
    }

    private String formatDoctorDisplayName(String realname) {
        String name = realname == null ? "" : realname.trim();
        if (name.equalsIgnoreCase("doctor")) {
            return "张敏";
        }
        return name.isBlank() ? "接诊医生" : name;
    }
}
