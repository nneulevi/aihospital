package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.*;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.PatientService;
import com.neuedu.his.service.AuthService;
import com.neuedu.his.util.JwtUtil;
import com.neuedu.his.util.SnowflakeIdUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class PatientServiceImpl implements PatientService {

    @Autowired
    private PatientMapper patientMapper;
    @Autowired
    private RegisterMapper registerMapper;
    @Autowired
    private SchedulingMapper schedulingMapper;
    @Autowired
    private EmployeeMapper employeeMapper;
    @Autowired
    private RegistLevelMapper registLevelMapper;
    @Autowired
    private PrescriptionMapper prescriptionMapper;
    @Autowired
    private CheckRequestMapper checkRequestMapper;
    @Autowired
    private InspectionRequestMapper inspectionRequestMapper;
    @Autowired
    private DisposalRequestMapper disposalRequestMapper;
    @Autowired
    private MedicalTechnologyMapper medicalTechnologyMapper;
    @Autowired
    private DepartmentMapper departmentMapper;
    @Autowired
    private DrugInfoMapper drugInfoMapper;
    @Autowired
    private PrescriptionDetailMapper prescriptionDetailMapper;
    @Autowired
    private AuthService authService;

    @Override
    public void sendCode(SendCodeRequestDTO request) {
        authService.sendCode(request);
    }

    @Override
    public LoginResponseVO authRegister(PatientAuthRegisterRequestDTO request) {
        return authService.patientAuthRegister(request);
    }

    @Override
    public void logout() {
        // JWT is stateless; clients clear the token locally.
    }

    @Override
    public String switchPatient(Integer patientId) {
        Patient patient = patientMapper.selectById(patientId);
        if (patient == null) {
            throw new BusinessException("patient does not exist");
        }
        return JwtUtil.generatePatientToken(patient.getId(), patient.getPhone(), patient.getCaseNumber());
    }

    @Override
    public List<PatientListVO> listPatients() {
        List<Patient> patients = patientMapper.selectAll();
        List<PatientListVO> list = new ArrayList<>();
        for (Patient patient : patients) {
            PatientListVO vo = new PatientListVO();
            vo.setPatientId(patient.getId());
            vo.setRealName(patient.getRealName());
            vo.setCaseNumber(patient.getCaseNumber());
            vo.setPhone(patient.getPhone());
            vo.setGender(patient.getGender());
            list.add(vo);
        }
        return list;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Integer register(PatientRegisterRequestDTO request) {
        String normalizedNoon = normalizeNoon(request.getNoon());
        Patient patient = patientMapper.selectByCardNumber(request.getCardNumber());
        if (patient == null) {
            patient = new Patient();
            patient.setCaseNumber(String.valueOf(SnowflakeIdUtil.nextId()));
            patient.setRealName(request.getRealName());
            patient.setGender(request.getGender());
            patient.setCardNumber(request.getCardNumber());
            patient.setBirthdate(request.getBirthdate());
            patient.setPhone(request.getPhone());
            patient.setHomeAddress(request.getHomeAddress());
            patientMapper.insert(patient);
        }

        List<Scheduling> available = schedulingMapper.selectAvailableDoctors(
                request.getDeptId(), request.getVisitDate(), normalizedNoon);
        Scheduling matchedSchedule = available.stream()
                .filter(s -> s.getEmployeeId().equals(request.getDoctorId()))
                .findFirst()
                .orElse(null);
        if (matchedSchedule == null) {
            throw new BusinessException("该医生当前时段不可预约");
        }
        int usedQuota = registerMapper.countActiveBySchedule(
                request.getDeptId(), request.getDoctorId(), request.getVisitDate(), normalizedNoon);
        int totalQuota = matchedSchedule.getRegistQuota() == null ? 0 : matchedSchedule.getRegistQuota();
        if (usedQuota >= totalQuota) {
            throw new BusinessException("该医生当前时段号源已满，请选择其他医生或时间");
        }
        int duplicated = registerMapper.countActiveByPatientSchedule(
                patient.getId(), request.getDeptId(), request.getDoctorId(), request.getVisitDate(), normalizedNoon);
        if (duplicated > 0) {
            throw new BusinessException("您已预约该医生当前时段，请勿重复挂号");
        }
        int duplicatedSameDoctor = registerMapper.countActiveByPatientDoctorDate(
                patient.getId(), request.getDoctorId(), request.getVisitDate());
        if (duplicatedSameDoctor > 0) {
            throw new BusinessException("您已预约该医生当日门诊，请勿重复进入同一医生就诊队列");
        }

        RegistLevel level = registLevelMapper.selectById(request.getRegistLevelId());
        if (level == null) {
            throw new BusinessException("挂号级别不存在");
        }

        Register register = new Register();
        register.setVisitNo(String.valueOf(SnowflakeIdUtil.nextId()));
        register.setPatientId(patient.getId());
        register.setVisitDate(request.getVisitDate());
        register.setNoon(normalizedNoon);
        register.setDeptmentId(request.getDeptId());
        register.setEmployeeId(request.getDoctorId());
        register.setRegistLevelId(request.getRegistLevelId());
        register.setSettleCategoryId(request.getSettleCategoryId());
        register.setSourceType("APP");
        register.setQueueNo(usedQuota + 1);
        register.setRegistMethod(request.getRegistMethod());
        register.setRegistMoney(level.getRegistFee());
        register.setVisitState("REGISTERED");

        registerMapper.insert(register);
        return register.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void cancelRegister(RegisterCancelRequestDTO request) {
        Register register = registerMapper.selectCancelableById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("该挂号记录不存在或已无法退号");
        }

        List<CheckRequest> checks = checkRequestMapper.selectByRegisterId(request.getRegisterId());
        List<Prescription> prescriptions = prescriptionMapper.selectByRegisterId(request.getRegisterId());
        if (!checks.isEmpty() || !prescriptions.isEmpty()) {
            throw new BusinessException("已开立检查或处方，请先退检查/处方后再退号");
        }

        registerMapper.cancelRegister(request.getRegisterId(), request.getCancelReason());
    }

    @Override
    public PageResult<PatientRecordListVO> getRecords(PatientRecordsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<Register> list = registerMapper.selectPatientRecords(
                query.getPatientId(), query.getStartDate(), query.getEndDate(), query.getVisitState());
        PageInfo<Register> pageInfo = new PageInfo<>(list);

        List<PatientRecordListVO> voList = new ArrayList<>();
        for (Register r : list) {
            PatientRecordListVO vo = new PatientRecordListVO();
            vo.setRegisterId(r.getId());
            vo.setVisitDate(r.getVisitDate() == null ? null : r.getVisitDate().toString());
            vo.setDeptName(r.getDeptName());
            vo.setDoctorName(r.getDoctorName());
            vo.setDiagnosis(r.getDiagnosis());
            vo.setVisitState(r.getVisitState());
            vo.setVisitStateName(formatVisitState(r.getVisitState()));
            voList.add(vo);
        }

        PageResult<PatientRecordListVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    @Override
    public PatientRecordListVO getRecordDetail(Integer registerId) {
        Register register = registerMapper.selectVisitDetail(registerId);
        if (register == null) {
            throw new BusinessException("就诊记录不存在");
        }
        PatientRecordListVO vo = new PatientRecordListVO();
        vo.setRegisterId(register.getId());
        vo.setVisitDate(register.getVisitDate() == null ? null : register.getVisitDate().toString());
        vo.setDeptName(register.getDeptName());
        vo.setDoctorName(register.getDoctorName());
        vo.setDiagnosis(register.getDiagnosis());
        vo.setVisitState(register.getVisitState());
        vo.setVisitStateName(formatVisitState(register.getVisitState()));
        return vo;
    }

    @Override
    public PageResult<DoctorListVO> getDoctors(DoctorListQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        String normalizedNoon = normalizeNoon(query.getNoon());
        List<Scheduling> list = schedulingMapper.selectAvailableDoctors(
                query.getDeptId(), query.getVisitDate(), normalizedNoon);
        PageInfo<Scheduling> pageInfo = new PageInfo<>(list);

        List<DoctorListVO> voList = new ArrayList<>();
        for (Scheduling s : list) {
            DoctorListVO vo = new DoctorListVO();
            vo.setDoctorId(s.getEmployeeId());
            vo.setDeptId(s.getDeptmentId());
            Department department = s.getDeptmentId() == null ? null : departmentMapper.selectById(s.getDeptmentId());
            if (department != null) {
                vo.setDeptName(department.getDeptName());
            }
            Employee emp = employeeMapper.selectById(s.getEmployeeId());
            if (emp != null) {
                vo.setDoctorName(formatDoctorDisplayName(emp.getRealname()));
                vo.setTitleLevel(formatDoctorTitle(emp.getTitleLevel()));
            }
            vo.setSpecialty(formatDoctorSpecialty(department == null ? null : department.getDeptName(), vo.getTitleLevel()));
            vo.setScheduleDate(s.getScheduleDate());
            vo.setNoon(s.getNoon());
            vo.setRegistQuota(s.getRegistQuota());
            int usedQuota = registerMapper.countActiveBySchedule(
                    s.getDeptmentId(), s.getEmployeeId(), s.getScheduleDate(), normalizeNoon(s.getNoon()));
            vo.setRemainingQuota(Math.max(0, (s.getRegistQuota() == null ? 0 : s.getRegistQuota()) - usedQuota));
            voList.add(vo);
        }

        PageResult<DoctorListVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    @Override
    public PageResult<OrderListVO> getOrders(PatientOrdersQueryDTO query) {
        List<OrderListVO> voList = new ArrayList<>();

        List<Register> registers = registerMapper.selectPatientRecords(
                query.getPatientId(), null, null, null);

        for (Register register : registers) {
            Integer registerId = register.getId();

            List<CheckRequest> checks = checkRequestMapper.selectByRegisterId(registerId);
            for (CheckRequest check : checks) {
                String orderState = mapOrderState(check.getCheckState());
                if (orderState != null) {
                    OrderListVO vo = new OrderListVO();
                    vo.setRegisterId(registerId);
                    vo.setItemType("CHECK");
                    MedicalTechnology tech = medicalTechnologyMapper.selectById(check.getMedicalTechnologyId());
                    vo.setItemName(tech != null && tech.getTechName() != null ? tech.getTechName() : "检查项目");
                    vo.setItemId(check.getId());
                    vo.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
                    vo.setOrderState(orderState);
                    voList.add(vo);
                }
            }

            List<InspectionRequest> inspections = inspectionRequestMapper.selectByRegisterId(registerId);
            for (InspectionRequest inspection : inspections) {
                String orderState = mapOrderState(inspection.getInspectionState());
                if (orderState != null) {
                    OrderListVO vo = new OrderListVO();
                    vo.setRegisterId(registerId);
                    vo.setItemType("INSPECTION");
                    MedicalTechnology tech = medicalTechnologyMapper.selectById(inspection.getMedicalTechnologyId());
                    vo.setItemName(tech != null && tech.getTechName() != null ? tech.getTechName() : "检验项目");
                    vo.setItemId(inspection.getId());
                    vo.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
                    vo.setOrderState(orderState);
                    voList.add(vo);
                }
            }

            List<DisposalRequest> disposals = disposalRequestMapper.selectByRegisterId(registerId);
            for (DisposalRequest disposal : disposals) {
                String orderState = mapOrderState(disposal.getDisposalState());
                if (orderState != null) {
                    OrderListVO vo = new OrderListVO();
                    vo.setRegisterId(registerId);
                    vo.setItemType("DISPOSAL");
                    MedicalTechnology tech = medicalTechnologyMapper.selectById(disposal.getMedicalTechnologyId());
                    vo.setItemName(tech != null && tech.getTechName() != null ? tech.getTechName() : "处置项目");
                    vo.setItemId(disposal.getId());
                    vo.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
                    vo.setOrderState(orderState);
                    voList.add(vo);
                }
            }

            List<Prescription> prescriptions = prescriptionMapper.selectByRegisterId(registerId);
            for (Prescription prescription : prescriptions) {
                String orderState = mapOrderState(prescription.getPrescriptionStatus());
                if (orderState != null) {
                    OrderListVO vo = new OrderListVO();
                    vo.setRegisterId(registerId);
                    vo.setItemType("PRESCRIPTION");
                    vo.setItemName("处方");
                    vo.setItemId(prescription.getId());
                    vo.setAmount(prescription.getTotalAmount());
                    vo.setOrderState(orderState);
                    voList.add(vo);
                }
            }
        }

        if (query.getOrderState() != null) {
            voList = voList.stream()
                    .filter(v -> query.getOrderState().equals(v.getOrderState()))
                    .collect(Collectors.toList());
        }

        long total = voList.size();
        int pageNum = query.getPageNum() == null ? 1 : query.getPageNum();
        int pageSize = query.getPageSize() == null ? 10 : query.getPageSize();
        int fromIndex = Math.max(0, (pageNum - 1) * pageSize);
        int toIndex = Math.min(voList.size(), fromIndex + pageSize);
        List<OrderListVO> pageRecords = fromIndex >= voList.size() ? new ArrayList<>() : voList.subList(fromIndex, toIndex);

        PageResult<OrderListVO> result = new PageResult<>();
        result.setTotal(total);
        result.setPageNum(pageNum);
        result.setPageSize(pageSize);
        result.setTotalPages((int) Math.ceil(total * 1.0 / pageSize));
        result.setRecords(pageRecords);
        return result;
    }

    @Override
    public List<PatientDepartmentVO> getDepartments() {
        Map<String, Department> visibleDepartments = new LinkedHashMap<>();
        for (Department department : departmentMapper.selectByType("CLINICAL")) {
            if (!isPatientVisibleDepartment(department)) {
                continue;
            }
            String key = normalizeDeptName(department.getDeptName());
            Department current = visibleDepartments.get(key);
            if (current == null || (!hasUpcomingSchedule(current) && hasUpcomingSchedule(department))) {
                visibleDepartments.put(key, department);
            }
        }
        return visibleDepartments.values().stream().map(department -> {
            PatientDepartmentVO vo = new PatientDepartmentVO();
            vo.setDeptId(department.getId());
            vo.setDeptName(department.getDeptName());
            vo.setDeptType(department.getDeptType());
            vo.setDescription(formatDeptDescription(department.getDeptType()));
            return vo;
        }).collect(Collectors.toList());
    }

    @Override
    public PatientTodayRegisterVO getTodayRegister(Integer patientId) {
        Register register = findTodayRegister(patientId, null);
        return register == null ? null : toTodayRegisterVO(register);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public PatientCheckinResultVO submitCheckin(Integer patientId, Integer registerId) {
        Register register = findTodayRegister(patientId, registerId);
        if (register == null) {
            throw new BusinessException("当前没有可报道的今日挂号记录");
        }
        if ("REGISTERED".equals(register.getVisitState())) {
            registerMapper.updateState(register.getId(), "CHECKED_IN");
            register.setVisitState("CHECKED_IN");
        }
        PatientCheckinResultVO vo = new PatientCheckinResultVO();
        vo.setRegisterId(register.getId());
        vo.setVisitState(register.getVisitState());
        vo.setVisitStateName(formatVisitState(register.getVisitState()));
        vo.setQueueNo(register.getQueueNo());
        vo.setDeptName(register.getDeptName());
        vo.setDoctorName(register.getDoctorName());
        vo.setMessage("报道成功，请在候诊区等待叫号。");
        return vo;
    }

    @Override
    public PatientQueueStatusVO getQueueStatus(Integer patientId, Integer registerId) {
        Register register = findTodayRegister(patientId, registerId);
        if (register == null) {
            PatientQueueStatusVO empty = new PatientQueueStatusVO();
            empty.setPatientId(patientId);
            empty.setWaitingAhead(0);
            empty.setMessage("当前没有进行中的候诊记录。");
            return empty;
        }
        PatientQueueStatusVO vo = new PatientQueueStatusVO();
        vo.setRegisterId(register.getId());
        vo.setPatientId(register.getPatientId());
        vo.setVisitDate(register.getVisitDate());
        vo.setNoon(register.getNoon());
        vo.setDeptName(register.getDeptName());
        vo.setDoctorName(register.getDoctorName());
        vo.setQueueNo(register.getQueueNo());
        vo.setVisitState(register.getVisitState());
        vo.setVisitStateName(formatVisitState(register.getVisitState()));
        int waitingAhead = registerMapper.countWaitingAhead(
                register.getDeptmentId(),
                register.getEmployeeId(),
                register.getVisitDate(),
                register.getNoon(),
                register.getQueueNo() == null ? 0 : register.getQueueNo());
        vo.setWaitingAhead(Math.max(0, waitingAhead));
        vo.setMessage(waitingAhead > 0
                ? "前方还有 " + waitingAhead + " 位患者，请留意叫号。"
                : "已接近就诊顺序，请在诊区等候。");
        return vo;
    }

    @Override
    public List<DeptQueueVO> getQueueDepts(Integer patientId) {
        List<DeptQueueVO> result = new ArrayList<>();
        for (Register register : registerMapper.selectPatientRecords(patientId, null, null, null)) {
            if (register.getDeptmentId() == null || register.getDeptName() == null) {
                continue;
            }
            boolean exists = result.stream().anyMatch(item -> register.getDeptmentId().equals(item.getDeptId()));
            if (!exists) {
                DeptQueueVO vo = new DeptQueueVO();
                vo.setDeptId(register.getDeptmentId());
                vo.setDeptName(register.getDeptName());
                vo.setActiveQueueCount(registerMapper.countWaitingAhead(
                        register.getDeptmentId(),
                        register.getEmployeeId(),
                        register.getVisitDate(),
                        register.getNoon(),
                        Integer.MAX_VALUE));
                result.add(vo);
            }
        }
        return result;
    }

    @Override
    public QueueCountVO getQueueCount(Integer patientId) {
        PatientQueueStatusVO status = getQueueStatus(patientId, null);
        QueueCountVO vo = new QueueCountVO();
        vo.setPatientId(patientId);
        vo.setRegisterId(status.getRegisterId());
        vo.setQueueCount(status.getWaitingAhead() == null ? 0 : status.getWaitingAhead());
        vo.setVisitState(status.getVisitState());
        vo.setVisitStateName(status.getVisitStateName());
        return vo;
    }

    @Override
    public List<PatientMedicalTechnologyVO> getMedicalTechnologies(String techType, Integer deptId) {
        List<MedicalTechnology> technologies = deptId == null
                ? medicalTechnologyMapper.selectByType(techType)
                : medicalTechnologyMapper.selectByDept(deptId).stream()
                .filter(item -> techType.equals(item.getTechType()))
                .collect(Collectors.toList());
        Map<String, MedicalTechnology> visible = new LinkedHashMap<>();
        for (MedicalTechnology technology : technologies) {
            if (!isPatientVisibleMedicalTechnology(technology)) {
                continue;
            }
            String key = deptId == null ? medicalTechnologyDisplayKey(technology) : String.valueOf(technology.getId());
            MedicalTechnology existing = visible.get(key);
            if (existing == null || shouldPreferMedicalTechnology(technology, existing)) {
                visible.put(key, technology);
            }
        }
        return visible.values().stream().map(this::toMedicalTechnologyVO).collect(Collectors.toList());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createCheckRequest(PatientCheckRequestDTO request) {
        Register register = requirePatientRegister(request.getPatientId(), request.getRegisterId());
        for (Integer technologyId : request.getMedicalTechnologyIds()) {
            MedicalTechnology technology = medicalTechnologyMapper.selectById(technologyId);
            if (technology == null || !"CHECK".equals(technology.getTechType())) {
                throw new BusinessException("检查项目不存在或类型不正确：" + technologyId);
            }
            CheckRequest check = new CheckRequest();
            check.setRegisterId(register.getId());
            check.setMedicalTechnologyId(technologyId);
            check.setCheckInfo("患者端预约：" + technology.getTechName());
            check.setCheckPosition("按项目要求");
            checkRequestMapper.insert(check);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createInspectionRequest(PatientInspectionRequestDTO request) {
        Register register = requirePatientRegister(request.getPatientId(), request.getRegisterId());
        for (Integer technologyId : request.getMedicalTechnologyIds()) {
            MedicalTechnology technology = medicalTechnologyMapper.selectById(technologyId);
            if (technology == null || !"INSPECTION".equals(technology.getTechType())) {
                throw new BusinessException("检验项目不存在或类型不正确：" + technologyId);
            }
            InspectionRequest inspection = new InspectionRequest();
            inspection.setRegisterId(register.getId());
            inspection.setMedicalTechnologyId(technologyId);
            inspection.setInspectionInfo("患者端预约：" + technology.getTechName());
            inspection.setInspectionPosition("按项目要求");
            inspectionRequestMapper.insert(inspection);
        }
    }

    @Override
    public PageResult<PatientMedicalRequestVO> getInspectionRequests(Integer patientId, Integer pageNum, Integer pageSize) {
        List<PatientMedicalRequestVO> requests = collectMedicalRequests(patientId, "INSPECTION");
        return pageOf(requests, pageNum, pageSize);
    }

    @Override
    public PageResult<PatientMedicalRequestVO> getCheckRequests(Integer patientId, Integer pageNum, Integer pageSize) {
        List<PatientMedicalRequestVO> requests = collectMedicalRequests(patientId, "CHECK");
        return pageOf(requests, pageNum, pageSize);
    }

    @Override
    public PageResult<PatientPrescriptionVO> getPrescriptions(Integer patientId, Integer pageNum, Integer pageSize) {
        List<PatientPrescriptionVO> prescriptions = new ArrayList<>();
        for (Register register : registerMapper.selectPatientRecords(patientId, null, null, null)) {
            for (Prescription prescription : prescriptionMapper.selectByRegisterId(register.getId())) {
                PatientPrescriptionVO vo = new PatientPrescriptionVO();
                vo.setPrescriptionId(prescription.getId());
                vo.setRegisterId(register.getId());
                vo.setPrescriptionNo(prescription.getPrescriptionNo());
                vo.setStatus(prescription.getPrescriptionStatus());
                vo.setStatusName(formatChargeState(prescription.getPrescriptionStatus()));
                vo.setTotalAmount(prescription.getTotalAmount());
                vo.setDoctorName(register.getDoctorName());
                vo.setCreationTime(prescription.getCreationTime());
                vo.setDispenseTime(prescription.getDispenseTime());
                List<String> drugNames = prescriptionDetailMapper.selectByPrescriptionId(prescription.getId()).stream()
                        .map(detail -> drugInfoMapper.selectById(detail.getDrugId()))
                        .filter(drug -> drug != null && drug.getDrugName() != null)
                        .map(DrugInfo::getDrugName)
                        .distinct()
                        .collect(Collectors.toList());
                vo.setDrugNames(drugNames);
                vo.setDrugSummary(drugNames.isEmpty() ? "处方明细待药房确认" : String.join("、", drugNames));
                prescriptions.add(vo);
            }
        }
        return pageOf(prescriptions, pageNum, pageSize);
    }

    @Override
    public PrescriptionDetailVO getPrescriptionDetail(Integer prescriptionId) {
        Prescription prescription = prescriptionMapper.selectById(prescriptionId);
        if (prescription == null) {
            throw new BusinessException("处方不存在");
        }
        Register register = registerMapper.selectVisitDetail(prescription.getRegisterId());
        PrescriptionDetailVO vo = new PrescriptionDetailVO();
        vo.setPrescriptionId(prescription.getId());
        vo.setRegisterId(prescription.getRegisterId());
        vo.setPrescriptionNo(prescription.getPrescriptionNo());
        vo.setStatus(prescription.getPrescriptionStatus());
        vo.setStatusName(formatChargeState(prescription.getPrescriptionStatus()));
        vo.setTotalAmount(prescription.getTotalAmount());
        vo.setCreationTime(prescription.getCreationTime());
        vo.setDispenseTime(prescription.getDispenseTime());
        if (register != null) {
            vo.setDeptName(register.getDeptName());
            vo.setDoctorName(register.getDoctorName());
            vo.setPatientName(register.getRealName());
        }
        for (PrescriptionDetail detail : prescriptionDetailMapper.selectByPrescriptionId(prescription.getId())) {
            DrugInfo drug = drugInfoMapper.selectById(detail.getDrugId());
            PrescriptionDetailVO.PrescriptionDrugDetailVO drugVO = new PrescriptionDetailVO.PrescriptionDrugDetailVO();
            drugVO.setDrugId(detail.getDrugId());
            drugVO.setDrugName(drug == null ? "未知药品" : drug.getDrugName());
            drugVO.setSpecification(drug == null ? null : drug.getDrugFormat());
            drugVO.setDosage(detail.getSingleDose());
            drugVO.setFrequency(detail.getFrequency());
            drugVO.setDays(detail.getUseDays());
            drugVO.setQuantity(detail.getDrugNumber());
            drugVO.setPrice(drug == null ? BigDecimal.ZERO : drug.getDrugPrice());
            vo.getDrugs().add(drugVO);
        }
        return vo;
    }

    @Override
    public PageResult<PatientReportVO> getReports(Integer patientId, Integer pageNum, Integer pageSize) {
        List<PatientReportVO> reports = new ArrayList<>();
        for (Register register : registerMapper.selectPatientRecords(patientId, null, null, null)) {
            for (PatientMedicalRequestVO request : collectRegisterMedicalRequests(register, "CHECK")) {
                reports.add(toPatientReport(register, request));
            }
            for (PatientMedicalRequestVO request : collectRegisterMedicalRequests(register, "INSPECTION")) {
                reports.add(toPatientReport(register, request));
            }
        }
        return pageOf(reports, pageNum, pageSize);
    }

    @Override
    public ReportDetailVO getReportDetail(String reportId) {
        PatientReportVO report = findReportById(reportId);
        if (report == null) {
            throw new BusinessException("报告不存在");
        }
        Register register = registerMapper.selectVisitDetail(report.getRegisterId());
        ReportDetailVO vo = new ReportDetailVO();
        vo.setReportId(report.getReportId());
        vo.setRegisterId(report.getRegisterId());
        vo.setReportTitle(report.getItemName() + "报告");
        vo.setRequestType(report.getItemType());
        vo.setRequestTypeName("CHECK".equals(report.getItemType()) ? "检查" : "检验");
        vo.setDeptName(report.getDeptName());
        vo.setDoctorName(report.getDoctorName());
        vo.setPatientName(register == null ? null : register.getRealName());
        vo.setReportTime(report.getReportTime());
        vo.setReportText(report.getResult() == null || report.getResult().isBlank() ? "报告尚未完成，请以医技科室签发结果为准。" : report.getResult());
        vo.setViewed(Boolean.TRUE);
        vo.setReportFileUrl(null);
        return vo;
    }

    @Override
    public void markReportRead(String reportId) {
        if (findReportById(reportId) == null) {
            throw new BusinessException("报告不存在");
        }
    }

    @Override
    public PatientCurrentVO getCurrentPatient(Integer patientId) {
        Patient patient = patientMapper.selectById(patientId);
        if (patient == null) {
            throw new BusinessException("患者不存在");
        }
        PatientCurrentVO vo = new PatientCurrentVO();
        vo.setPatientId(patient.getId());
        vo.setRealName(patient.getRealName());
        vo.setPhone(patient.getPhone());
        vo.setCaseNumber(patient.getCaseNumber());
        return vo;
    }

    @Override
    public void bookInspectionRequest(BookRequestDTO request) {
        InspectionRequest inspection = inspectionRequestMapper.selectById(request.getRequestId());
        if (inspection == null) {
            throw new BusinessException("检验申请不存在");
        }
    }

    @Override
    public void bookCheckRequest(BookRequestDTO request) {
        CheckRequest check = checkRequestMapper.selectById(request.getRequestId());
        if (check == null) {
            throw new BusinessException("检查申请不存在");
        }
    }

    private String mapOrderState(String sourceState) {
        if ("CREATED".equals(sourceState)) {
            return "UNPAID";
        }
        if ("CHARGED".equals(sourceState) || "PAID".equals(sourceState) || "DISPENSED".equals(sourceState)) {
            return "PAID";
        }
        if ("REFUNDED".equals(sourceState)) {
            return "REFUNDED";
        }
        if ("CANCELLED".equals(sourceState)) {
            return "REFUNDED";
        }
        return null;
    }

    private Register findTodayRegister(Integer patientId, Integer registerId) {
        if (registerId != null) {
            Register register = registerMapper.selectVisitDetail(registerId);
            if (register == null || !patientId.equals(register.getPatientId())) {
                return null;
            }
            return register;
        }
        return registerMapper.selectLatestTodayByPatient(patientId, LocalDate.now());
    }

    private Register requirePatientRegister(Integer patientId, Integer registerId) {
        Register register = registerMapper.selectVisitDetail(registerId);
        if (register == null || !patientId.equals(register.getPatientId())) {
            throw new BusinessException("挂号记录不存在或不属于当前患者");
        }
        if ("REFUNDED".equals(register.getVisitState()) || "CANCELLED".equals(register.getVisitState())) {
            throw new BusinessException("当前挂号状态不可预约项目");
        }
        return register;
    }

    private PatientReportVO findReportById(String reportId) {
        if (reportId == null || !reportId.contains("-")) {
            return null;
        }
        String[] parts = reportId.split("-", 2);
        if (parts.length != 2) {
            return null;
        }
        Integer itemId;
        try {
            itemId = Integer.valueOf(parts[1]);
        } catch (NumberFormatException ex) {
            return null;
        }
        if ("CHECK".equals(parts[0])) {
            CheckRequest check = checkRequestMapper.selectById(itemId);
            if (check == null) {
                return null;
            }
            Register register = registerMapper.selectVisitDetail(check.getRegisterId());
            if (register == null) {
                return null;
            }
            for (PatientMedicalRequestVO request : collectRegisterMedicalRequests(register, "CHECK")) {
                if (itemId.equals(request.getRequestId())) {
                    return toPatientReport(register, request);
                }
            }
        }
        if ("INSPECTION".equals(parts[0])) {
            InspectionRequest inspection = inspectionRequestMapper.selectById(itemId);
            if (inspection == null) {
                return null;
            }
            Register register = registerMapper.selectVisitDetail(inspection.getRegisterId());
            if (register == null) {
                return null;
            }
            for (PatientMedicalRequestVO request : collectRegisterMedicalRequests(register, "INSPECTION")) {
                if (itemId.equals(request.getRequestId())) {
                    return toPatientReport(register, request);
                }
            }
        }
        return null;
    }

    private PatientTodayRegisterVO toTodayRegisterVO(Register register) {
        PatientTodayRegisterVO vo = new PatientTodayRegisterVO();
        vo.setRegisterId(register.getId());
        vo.setVisitNo(register.getVisitNo());
        vo.setPatientId(register.getPatientId());
        vo.setVisitDate(register.getVisitDate());
        vo.setNoon(register.getNoon());
        vo.setQueueNo(register.getQueueNo());
        vo.setVisitState(register.getVisitState());
        vo.setVisitStateName(formatVisitState(register.getVisitState()));
        vo.setDeptName(register.getDeptName());
        vo.setDoctorName(register.getDoctorName());
        vo.setCreateTime(register.getCreateTime());
        return vo;
    }

    private PatientMedicalTechnologyVO toMedicalTechnologyVO(MedicalTechnology technology) {
        PatientMedicalTechnologyVO vo = new PatientMedicalTechnologyVO();
        vo.setTechId(technology.getId());
        vo.setTechCode(technology.getTechCode());
        vo.setTechName(technology.getTechName());
        vo.setTechFormat(technology.getTechFormat());
        vo.setTechPrice(technology.getTechPrice());
        vo.setTechType(technology.getTechType());
        vo.setPriceType(technology.getPriceType());
        vo.setDeptId(technology.getDeptmentId());
        Department department = technology.getDeptmentId() == null ? null : departmentMapper.selectById(technology.getDeptmentId());
        vo.setDeptName(department == null ? null : department.getDeptName());
        return vo;
    }

    private List<PatientMedicalRequestVO> collectMedicalRequests(Integer patientId, String itemType) {
        List<PatientMedicalRequestVO> requests = new ArrayList<>();
        for (Register register : registerMapper.selectPatientRecords(patientId, null, null, null)) {
            requests.addAll(collectRegisterMedicalRequests(register, itemType));
        }
        return requests;
    }

    private List<PatientMedicalRequestVO> collectRegisterMedicalRequests(Register register, String itemType) {
        List<PatientMedicalRequestVO> requests = new ArrayList<>();
        if ("CHECK".equals(itemType)) {
            for (CheckRequest check : checkRequestMapper.selectByRegisterId(register.getId())) {
                MedicalTechnology tech = medicalTechnologyMapper.selectById(check.getMedicalTechnologyId());
                PatientMedicalRequestVO vo = new PatientMedicalRequestVO();
                vo.setRequestId(check.getId());
                vo.setRegisterId(register.getId());
                vo.setItemType("CHECK");
                vo.setItemName(tech != null ? tech.getTechName() : check.getCheckInfo());
                vo.setItemPosition(check.getCheckPosition());
                vo.setState(check.getCheckState());
                vo.setStateName(formatChargeState(check.getCheckState()));
                vo.setResult(check.getCheckResult());
                vo.setPrice(tech == null ? BigDecimal.ZERO : tech.getTechPrice());
                vo.setCreationTime(check.getCreationTime());
                requests.add(vo);
            }
        }
        if ("INSPECTION".equals(itemType)) {
            for (InspectionRequest inspection : inspectionRequestMapper.selectByRegisterId(register.getId())) {
                MedicalTechnology tech = medicalTechnologyMapper.selectById(inspection.getMedicalTechnologyId());
                PatientMedicalRequestVO vo = new PatientMedicalRequestVO();
                vo.setRequestId(inspection.getId());
                vo.setRegisterId(register.getId());
                vo.setItemType("INSPECTION");
                vo.setItemName(tech != null ? tech.getTechName() : inspection.getInspectionInfo());
                vo.setItemPosition(inspection.getInspectionPosition());
                vo.setState(inspection.getInspectionState());
                vo.setStateName(formatChargeState(inspection.getInspectionState()));
                vo.setResult(inspection.getInspectionResult());
                vo.setPrice(tech == null ? BigDecimal.ZERO : tech.getTechPrice());
                vo.setCreationTime(inspection.getCreationTime());
                requests.add(vo);
            }
        }
        return requests;
    }

    private PatientReportVO toPatientReport(Register register, PatientMedicalRequestVO request) {
        PatientReportVO vo = new PatientReportVO();
        vo.setReportId(request.getItemType() + "-" + request.getRequestId());
        vo.setRegisterId(register.getId());
        vo.setItemType(request.getItemType());
        vo.setItemId(request.getRequestId());
        vo.setItemName(request.getItemName());
        vo.setItemPosition(request.getItemPosition());
        vo.setStatus(request.getState());
        vo.setStatusName(request.getStateName());
        vo.setResult(request.getResult());
        vo.setDeptName(register.getDeptName());
        vo.setDoctorName(register.getDoctorName());
        vo.setCreationTime(request.getCreationTime());
        vo.setReportTime(request.getCreationTime());
        return vo;
    }

    private <T> PageResult<T> pageOf(List<T> source, Integer pageNum, Integer pageSize) {
        int currentPage = pageNum == null || pageNum < 1 ? 1 : pageNum;
        int currentSize = pageSize == null || pageSize < 1 ? 20 : pageSize;
        int fromIndex = Math.max(0, (currentPage - 1) * currentSize);
        int toIndex = Math.min(source.size(), fromIndex + currentSize);
        List<T> records = fromIndex >= source.size() ? new ArrayList<>() : source.subList(fromIndex, toIndex);

        PageResult<T> result = new PageResult<>();
        result.setTotal((long) source.size());
        result.setPageNum(currentPage);
        result.setPageSize(currentSize);
        result.setTotalPages((int) Math.ceil(source.size() * 1.0 / currentSize));
        result.setRecords(records);
        return result;
    }

    private String formatDeptDescription(String deptType) {
        if ("CLINICAL".equals(deptType)) {
            return "门诊诊疗、开立检查检验与处方。";
        }
        if ("MEDICAL_TECH".equals(deptType)) {
            return "检查检验与影像相关项目。";
        }
        return "院内业务科室。";
    }

    private boolean isPatientVisibleDepartment(Department department) {
        if (department == null || department.getDeptName() == null || department.getDeptName().isBlank()) {
            return false;
        }
        String name = department.getDeptName();
        return !name.contains("User Logic")
                && !name.contains("Extended")
                && !name.contains("项目验收")
                && !name.contains("验收")
                && !name.contains("测试");
    }

    private boolean isPatientVisibleMedicalTechnology(MedicalTechnology technology) {
        if (technology == null || technology.getTechName() == null || technology.getTechName().isBlank()) {
            return false;
        }
        return isCleanPatientBusinessText(technology.getTechCode())
                && isCleanPatientBusinessText(technology.getTechName())
                && isCleanPatientBusinessText(technology.getTechFormat())
                && isCleanPatientBusinessText(technology.getPriceType());
    }

    private String medicalTechnologyDisplayKey(MedicalTechnology technology) {
        return normalizeNullable(technology.getTechType()) + "|"
                + normalizeNullable(technology.getTechName()) + "|"
                + String.valueOf(technology.getTechPrice());
    }

    private boolean shouldPreferMedicalTechnology(MedicalTechnology candidate, MedicalTechnology existing) {
        boolean candidateBusiness = normalizeNullable(candidate.getTechCode()).startsWith("BIZ-");
        boolean existingBusiness = normalizeNullable(existing.getTechCode()).startsWith("BIZ-");
        if (candidateBusiness != existingBusiness) {
            return candidateBusiness;
        }
        Integer candidateId = candidate.getId() == null ? Integer.MAX_VALUE : candidate.getId();
        Integer existingId = existing.getId() == null ? Integer.MAX_VALUE : existing.getId();
        return candidateId < existingId;
    }

    private boolean isCleanPatientBusinessText(String value) {
        if (value == null) {
            return true;
        }
        return !value.contains("User Logic")
                && !value.contains("Extended")
                && !value.contains("E2E")
                && !value.contains("BIZFLOW-")
                && !value.contains("业务联动")
                && !value.contains("项目验收")
                && !value.contains("验收")
                && !value.contains("测试");
    }

    private String normalizeNullable(String value) {
        return value == null ? "" : value.trim();
    }

    private String normalizeDeptName(String deptName) {
        return deptName == null ? "" : deptName.trim();
    }

    private boolean hasUpcomingSchedule(Department department) {
        if (department == null || department.getId() == null) {
            return false;
        }
        LocalDate current = LocalDate.now();
        LocalDate end = current.plusDays(14);
        while (!current.isAfter(end)) {
            if (!schedulingMapper.selectAvailableDoctors(department.getId(), current, "AM").isEmpty()
                    || !schedulingMapper.selectAvailableDoctors(department.getId(), current, "PM").isEmpty()) {
                return true;
            }
            current = current.plusDays(1);
        }
        return false;
    }

    private String formatDoctorSpecialty(String deptName, String titleLevel) {
        String title = titleLevel == null || titleLevel.isBlank() ? "门诊诊疗" : titleLevel + "门诊诊疗";
        if (deptName == null) {
            return title;
        }
        if (deptName.contains("神经内")) {
            return title + "，擅长头痛、眩晕、脑血管病、高血压相关神经系统症状评估。";
        }
        if (deptName.contains("神经外")) {
            return title + "，擅长颅脑外伤、颅内占位、脑出血术前评估及头部 CT 结果复核。";
        }
        if (deptName.contains("急诊")) {
            return title + "，擅长突发头痛、意识障碍、外伤、急性胸痛腹痛等急危重症初筛。";
        }
        if (deptName.contains("呼吸")) {
            return title + "，擅长咳嗽、发热、气促、肺部感染与慢性气道疾病诊疗。";
        }
        if (deptName.contains("消化")) {
            return title + "，擅长腹痛、恶心呕吐、腹泻、消化道出血等消化系统症状诊疗。";
        }
        return title + "，擅长" + deptName + "常见病、多发病诊疗。";
    }

    private String formatDoctorDisplayName(String realname) {
        String name = realname == null ? "" : realname.trim();
        if (name.equalsIgnoreCase("doctor")) {
            return "张敏";
        }
        return name.isBlank() ? "接诊医生" : name;
    }

    private String formatDoctorTitle(String titleLevel) {
        String title = titleLevel == null ? "" : titleLevel.trim();
        if (title.equalsIgnoreCase("doctor")) {
            return "主任医师";
        }
        return title.isBlank() ? "医师" : title;
    }

    private String formatChargeState(String state) {
        if ("CREATED".equals(state)) {
            return "待缴费";
        }
        if ("CHARGED".equals(state) || "PAID".equals(state)) {
            return "已缴费";
        }
        if ("EXECUTING".equals(state)) {
            return "执行中";
        }
        if ("COMPLETED".equals(state)) {
            return "已完成";
        }
        if ("DISPENSED".equals(state)) {
            return "已发药";
        }
        if ("REFUNDED".equals(state)) {
            return "已退费";
        }
        if ("CANCELLED".equals(state)) {
            return "已取消";
        }
        return state;
    }

    private String normalizeNoon(String noon) {
        if ("MORNING".equalsIgnoreCase(noon)) {
            return "AM";
        }
        if ("AFTERNOON".equalsIgnoreCase(noon)) {
            return "PM";
        }
        return noon;
    }

    private String formatVisitState(String visitState) {
        if ("REGISTERED".equals(visitState)) {
            return "已挂号";
        }
        if ("CHECKED_IN".equals(visitState)) {
            return "已报道";
        }
        if ("DOCTOR_RECEIVED".equals(visitState) || "ONGOING".equals(visitState) || "CONSULTING".equals(visitState)) {
            return "就诊中";
        }
        if ("DIAGNOSED".equals(visitState) || "DIAGNOSIS_DONE".equals(visitState)) {
            return "已确诊";
        }
        if ("FINISHED".equals(visitState)) {
            return "已完成";
        }
        if ("REFUNDED".equals(visitState)) {
            return "已退号";
        }
        if ("CANCELLED".equals(visitState)) {
            return "已取消";
        }
        return visitState;
    }
}
