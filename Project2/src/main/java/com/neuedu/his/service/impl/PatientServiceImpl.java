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
import java.util.ArrayList;
import java.util.List;
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
                request.getDeptId(), request.getVisitDate(), request.getNoon());
        boolean doctorAvailable = available.stream()
                .anyMatch(s -> s.getEmployeeId().equals(request.getDoctorId()));
        if (!doctorAvailable) {
            throw new BusinessException("该医生当前时段不可预约");
        }

        RegistLevel level = registLevelMapper.selectById(request.getRegistLevelId());
        if (level == null) {
            throw new BusinessException("挂号级别不存在");
        }

        Register register = new Register();
        register.setVisitNo(String.valueOf(SnowflakeIdUtil.nextId()));
        register.setPatientId(patient.getId());
        register.setVisitDate(request.getVisitDate());
        register.setNoon(request.getNoon());
        register.setDeptmentId(request.getDeptId());
        register.setEmployeeId(request.getDoctorId());
        register.setRegistLevelId(request.getRegistLevelId());
        register.setSettleCategoryId(request.getSettleCategoryId());
        register.setSourceType("APP");
        register.setQueueNo(available.size() + 1);
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
            vo.setVisitDate(r.getVisitDate().toString());
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
        return vo;
    }

    @Override
    public PageResult<DoctorListVO> getDoctors(DoctorListQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<Scheduling> list = schedulingMapper.selectAvailableDoctors(
                query.getDeptId(), query.getVisitDate(), query.getNoon());
        PageInfo<Scheduling> pageInfo = new PageInfo<>(list);

        List<DoctorListVO> voList = new ArrayList<>();
        for (Scheduling s : list) {
            DoctorListVO vo = new DoctorListVO();
            vo.setDoctorId(s.getEmployeeId());
            Employee emp = employeeMapper.selectById(s.getEmployeeId());
            if (emp != null) {
                vo.setDoctorName(emp.getRealname());
            }
            vo.setScheduleDate(s.getScheduleDate());
            vo.setNoon(s.getNoon());
            vo.setRegistQuota(s.getRegistQuota());
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
        return null;
    }
}
