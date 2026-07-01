package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.*;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.PatientService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class PatientServiceImpl implements PatientService {

    @Autowired
    private RegisterMapper registerMapper;

    @Autowired
    private PatientMapper patientMapper;

    @Autowired
    private DepartmentMapper departmentMapper;

    @Autowired
    private SchedulingMapper schedulingMapper;

    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private RegistLevelMapper registLevelMapper;

    @Autowired
    private MedicalTechnologyMapper medicalTechnologyMapper;

    @Autowired
    private PrescriptionMapper prescriptionMapper;

    @Autowired
    private PrescriptionDetailMapper prescriptionDetailMapper;

    @Autowired
    private MedicalReportMapper medicalReportMapper;

    @Autowired
    private InspectionRequestMapper inspectionRequestMapper;

    @Autowired
    private CheckRequestMapper checkRequestMapper;

    @Autowired
    private ChargeItemMapper chargeItemMapper;

    private static final DateTimeFormatter DATE_FORMATTER = DateTimeFormatter.ofPattern("yyyy-MM-dd");

    // ==================== 原有方法 ====================

    @Override
    @Transactional
    public Integer register(PatientRegisterRequestDTO request) {
        // 1. 获取患者信息
        Patient patient = patientMapper.selectById(request.getPatientId());
        if (patient == null) {
            throw new BusinessException("就诊人不存在");
        }

        // 2. 检查号源
        Scheduling scheduling = schedulingMapper.selectByDoctorAndDate(
                request.getDoctorId(),
                request.getVisitDate(),
                request.getNoon()
        );
        if (scheduling == null) {
            throw new BusinessException("该医生当天没有排班");
        }

        // 统计已挂号人数
        Integer registeredCount = registerMapper.countByScheduling(
                request.getDoctorId(),
                request.getVisitDate(),
                request.getNoon()
        );
        int remainingQuota = scheduling.getRegistQuota() - (registeredCount == null ? 0 : registeredCount);
        if (remainingQuota <= 0) {
            throw new BusinessException("号源已满");
        }

        // 3. 创建挂号记录
        Register register = new Register();
        register.setPatientId(request.getPatientId());
        register.setDeptmentId(request.getDeptId());
        register.setEmployeeId(request.getDoctorId());
        register.setVisitDate(request.getVisitDate().atStartOfDay());
        register.setNoon(request.getNoon());
        register.setVisitState("REGISTERED");
        register.setCheckinStatus(0);
        register.setQueueNo(registeredCount + 1);

        // 挂号费
        if (request.getRegistLevelId() != null) {
            RegistLevel level = registLevelMapper.selectById(request.getRegistLevelId());
            if (level != null) {
                register.setRegistMoney(level.getRegistFee());
            }
        } else {
            // 默认取医生的挂号级别
            Employee doctor = employeeMapper.selectById(request.getDoctorId());
            if (doctor != null && doctor.getRegistLevelId() != null) {
                RegistLevel level = registLevelMapper.selectById(doctor.getRegistLevelId());
                if (level != null) {
                    register.setRegistMoney(level.getRegistFee());
                }
            }
        }

        register.setSettleCategoryId(request.getSettleCategoryId() != null ? request.getSettleCategoryId() : 1);
        register.setRegistMethod(request.getRegistMethod() != null ? request.getRegistMethod() : "在线预约");

        registerMapper.insert(register);

        ChargeItem chargeItem = new ChargeItem();
        chargeItem.setSourceId(Long.valueOf(register.getId()));
        chargeItem.setSourceType("REGISTER");
        chargeItem.setRegisterId(Long.valueOf(register.getId()));
        chargeItem.setItemName("Register Fee");
        chargeItem.setItemType("REGISTER");
        chargeItem.setAmount(register.getRegistMoney());
        chargeItem.setStatus("PENDING");
        chargeItemMapper.insert(chargeItem);

        return register.getId();
    }

    @Override
    @Transactional
    public void cancelRegister(RegisterCancelRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }
        if (!"REGISTERED".equals(register.getVisitState())) {
            throw new BusinessException("当前状态不可取消");
        }
        register.setVisitState("CANCELLED");
        registerMapper.update(register);
    }

    @Override
    public PageResult<PatientRecordListVO> getRecords(PatientRecordsQueryDTO query) {
        int offset = (query.getPageNum() - 1) * query.getPageSize();

        List<PatientRecordListVO> list = registerMapper.selectPatientRecords(
                query.getPatientId(),
                query.getVisitState(),
                offset,
                query.getPageSize()
        );

        Long total = registerMapper.countPatientRecords(
                query.getPatientId(),
                query.getVisitState()
        );

        PageResult<PatientRecordListVO> result = new PageResult<>();
        result.setRecords(list);
        result.setTotal(total);
        result.setPageNum(query.getPageNum());
        result.setPageSize(query.getPageSize());
        int totalPages = (int) Math.ceil((double) total / query.getPageSize());
        result.setTotalPages(totalPages);
        return result;
    }

    @Override
    public PatientRecordListVO getRecordDetail(Integer registerId) {
        return registerMapper.selectPatientRecordDetail(registerId);
    }

    @Override
    public PageResult<DoctorListVO> getDoctors(DoctorListQueryDTO query) {
        int offset = (query.getPageNum() - 1) * query.getPageSize();

        List<DoctorListVO> list = schedulingMapper.selectDoctorList(
                query.getDeptId(),
                query.getVisitDate(),
                query.getNoon(),
                offset,
                query.getPageSize()
        );

        // 计算剩余号源
        for (DoctorListVO vo : list) {
            Integer registeredCount = registerMapper.countByScheduling(
                    vo.getDoctorId(),
                    query.getVisitDate(),
                    query.getNoon()
            );
            int remaining = vo.getRegistQuota() - (registeredCount == null ? 0 : registeredCount);
            vo.setRemainingQuota(Math.max(remaining, 0));
        }

        Long total = schedulingMapper.countDoctorList(
                query.getDeptId(),
                query.getVisitDate(),
                query.getNoon()
        );

        PageResult<DoctorListVO> result = new PageResult<>();
        result.setRecords(list);
        result.setTotal(total);
        result.setPageNum(query.getPageNum());
        result.setPageSize(query.getPageSize());
        int totalPages = (int) Math.ceil((double) total / query.getPageSize());
        result.setTotalPages(totalPages);
        return result;
    }

    @Override
    public PageResult<OrderListVO> getOrders(PatientOrdersQueryDTO query) {
        int offset = (query.getPageNum() - 1) * query.getPageSize();

        List<OrderListVO> list = new ArrayList<>();

        // 1. 挂号费
        List<OrderListVO> registerOrders = registerMapper.selectRegisterOrders(
                query.getPatientId(),
                query.getOrderState(),
                offset,
                query.getPageSize()
        );
        if (registerOrders != null) {
            list.addAll(registerOrders);
        }

        // 2. 药费
        List<OrderListVO> drugOrders = prescriptionMapper.selectDrugOrders(
                query.getPatientId(),
                query.getOrderState(),
                offset,
                query.getPageSize()
        );
        if (drugOrders != null) {
            list.addAll(drugOrders);
        }

        // 3. 检查费
        List<OrderListVO> checkOrders = checkRequestMapper.selectCheckOrders(
                query.getPatientId(),
                query.getOrderState(),
                offset,
                query.getPageSize()
        );
        if (checkOrders != null) {
            list.addAll(checkOrders);
        }

        // 4. 检验费
        List<OrderListVO> inspectionOrders = inspectionRequestMapper.selectInspectionOrders(
                query.getPatientId(),
                query.getOrderState(),
                offset,
                query.getPageSize()
        );
        if (inspectionOrders != null) {
            list.addAll(inspectionOrders);
        }

        // 排序：按创建时间倒序
        list.sort((a, b) -> {
            if (a.getCreateTime() == null) return 1;
            if (b.getCreateTime() == null) return -1;
            return b.getCreateTime().compareTo(a.getCreateTime());
        });

        // 分页
        int total = list.size();
        int start = (query.getPageNum() - 1) * query.getPageSize();
        int end = Math.min(start + query.getPageSize(), total);
        List<OrderListVO> pageList = total > 0 ? list.subList(start, end) : new ArrayList<>();

        PageResult<OrderListVO> result = new PageResult<>();
        result.setRecords(pageList);
        result.setTotal((long) total);
        result.setPageNum(query.getPageNum());
        result.setPageSize(query.getPageSize());
        int totalPages = (int) Math.ceil((double) total / query.getPageSize());
        result.setTotalPages(totalPages);
        return result;
    }

    // ==================== 新增方法 ====================

    @Override
    public List<DeptListVO> listDepartments() {
        List<Department> departments = departmentMapper.selectAll();
        return departments.stream()
                .filter(d -> d.getDelmark() != null && d.getDelmark())  // true 表示可用
                .map(d -> DeptListVO.fromDepartment(d.getId(), d.getDeptName()))
                .collect(Collectors.toList());
    }

    @Override
    public List<TodayRegisterVO> getTodayRegisters(Integer patientId) {
        LocalDate today = LocalDate.now();
        return registerMapper.selectTodayRegisters(patientId, today);
    }

    @Override
    @Transactional
    public CheckinResultVO submitCheckin(CheckinRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        if (!"REGISTERED".equals(register.getVisitState())) {
            throw new BusinessException("当前状态不可报到");
        }

        if (register.getCheckinStatus() == 1) {
            throw new BusinessException("已报到，请勿重复操作");
        }

        // 更新报到状态
        register.setCheckinStatus(1);
        register.setVisitState("CONSULTING");
        register.setCheckinTime(LocalDateTime.now());
        registerMapper.update(register);

        // 计算前面人数（同医生、同日、同午别，已报到且排队号小于当前）
        Integer aheadCount = registerMapper.countAhead(
                register.getEmployeeId(),
                register.getVisitDate(),
                register.getNoon(),
                register.getQueueNo()
        );

        CheckinResultVO result = new CheckinResultVO();
        result.setQueueNumber(String.format("%02d", register.getQueueNo()));
        result.setAheadCount(aheadCount != null ? aheadCount : 0);
        return result;
    }

    @Override
    public QueueStatusVO getQueueStatus(Integer registerId) {
        Register register = registerMapper.selectById(registerId);
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        // 获取当前科室的队列
        List<QueueItemVO> queueList = registerMapper.selectQueueList(
                register.getEmployeeId(),
                register.getVisitDate(),
                register.getNoon()
        );

        // 计算前面人数
        Integer aheadCount = registerMapper.countAhead(
                register.getEmployeeId(),
                register.getVisitDate(),
                register.getNoon(),
                register.getQueueNo()
        );

        // 获取当前叫号（取已报到的最小排队号）
        Integer currentCalling = registerMapper.getCurrentCalling(
                register.getEmployeeId(),
                register.getVisitDate(),
                register.getNoon()
        );

        // 获取科室名称
        Department dept = departmentMapper.selectById(register.getDeptmentId());

        QueueStatusVO result = new QueueStatusVO();
        result.setQueueNumber(String.format("%02d", register.getQueueNo()));
        result.setAheadCount(aheadCount != null ? aheadCount : 0);
        result.setCurrentCalling(currentCalling != null ? String.format("%02d", currentCalling) : "--");
        result.setCurrentRoom((currentCalling != null ? (currentCalling % 5 + 1) : 1) + "号诊室");
        result.setDeptName(dept != null ? dept.getDeptName() : "");
        result.setQueueList(queueList);
        return result;
    }

    @Override
    public List<DeptQueueVO> getQueueDepts(Integer patientId) {
        return registerMapper.selectQueueDepts(patientId);
    }

    @Override
    public List<MedicalTechVO> getInspectionList() {
        List<MedicalTechnology> list = medicalTechnologyMapper.selectByType("INSPECTION");
        return list.stream().map(this::toMedicalTechVO).collect(Collectors.toList());
    }

    @Override
    public List<MedicalTechVO> getCheckList() {
        List<MedicalTechnology> list = medicalTechnologyMapper.selectByType("CHECK");
        return list.stream().map(this::toMedicalTechVO).collect(Collectors.toList());
    }

    private MedicalTechVO toMedicalTechVO(MedicalTechnology tech) {
        MedicalTechVO vo = new MedicalTechVO();
        vo.setId(tech.getId());
        vo.setName(tech.getTechName());
        vo.setType(tech.getTechType());
        vo.setTypeName(getTypeName(tech.getTechType()));
        vo.setBodyPart(tech.getTechFormat());
        vo.setPrice(tech.getTechPrice());
        vo.setTips(getTips(tech.getTechName()));
        return vo;
    }

    private String getTypeName(String type) {
        if ("INSPECTION".equals(type)) return "检验科";
        if ("CHECK".equals(type)) return "检查科";
        if ("RADIOLOGY".equals(type)) return "放射科";
        if ("ULTRASOUND".equals(type)) return "超声科";
        if ("ENDOSCOPY".equals(type)) return "内镜科";
        if ("ECG".equals(type)) return "心电图";
        return "其他";
    }

    private String getTips(String techName) {
        if (techName == null) return "无需特殊准备";
        if (techName.contains("胃镜") || techName.contains("肠镜") || techName.contains("无痛胃")) {
            return "需空腹8小时以上，需家属陪同";
        }
        if (techName.contains("腹部") && techName.contains("彩超")) {
            return "需空腹8小时以上";
        }
        if (techName.contains("CT") && !techName.contains("增强")) {
            return "无需特殊准备";
        }
        if (techName.contains("动态心电图")) {
            return "需佩戴24小时";
        }
        if (techName.contains("运动平板")) {
            return "需穿运动鞋";
        }
        if (techName.contains("脑电图")) {
            return "需洗头、保持清醒";
        }
        return "无需特殊准备";
    }

    @Override
    @Transactional
    public void createInspectionRequest(PatientInspectionRequestDTO request) {
        for (Integer techId : request.getMedicalTechnologyIds()) {
            InspectionRequest inspectionRequest = new InspectionRequest();
            inspectionRequest.setRegisterId(request.getRegisterId());
            inspectionRequest.setMedicalTechnologyId(techId);
            inspectionRequest.setInspectionInfo("患者自助预约");
            inspectionRequest.setInspectionState("BOOKED");
            inspectionRequest.setIsSelfBooked(1);
            inspectionRequest.setBookedTime(request.getBookedTime());
            inspectionRequest.setCreationTime(LocalDateTime.now());
            inspectionRequestMapper.insert(inspectionRequest);
        }
    }

    @Override
    @Transactional
    public void createCheckRequest(PatientCheckRequestDTO request) {
        for (Integer techId : request.getMedicalTechnologyIds()) {
            CheckRequest checkRequest = new CheckRequest();
            checkRequest.setRegisterId(request.getRegisterId());
            checkRequest.setMedicalTechnologyId(techId);
            checkRequest.setCheckInfo("患者自助预约");
            checkRequest.setCheckState("BOOKED");
            checkRequest.setIsSelfBooked(1);
            checkRequest.setBookedTime(request.getBookedTime());
            checkRequest.setCreationTime(LocalDateTime.now());
            checkRequestMapper.insert(checkRequest);
        }
    }

    @Override
    public PageResult<PrescriptionListVO> getPrescriptions(PrescriptionQueryDTO query) {
        int offset = (query.getPageNum() - 1) * query.getPageSize();

        List<PrescriptionListVO> list = prescriptionMapper.selectPrescriptionList(
                query.getPatientId(),
                query.getStatus(),
                offset,
                query.getPageSize()
        );

        // 填充药品摘要
        for (PrescriptionListVO vo : list) {
            List<PrescriptionListVO.PrescriptionDrugSummaryVO> drugs =
                    prescriptionDetailMapper.selectDrugSummaryByPrescriptionId(vo.getId());
            vo.setDrugs(drugs);
        }

        Long total = prescriptionMapper.countPrescriptionList(
                query.getPatientId(),
                query.getStatus()
        );

        PageResult<PrescriptionListVO> result = new PageResult<>();
        result.setRecords(list);
        result.setTotal(total);
        result.setPageNum(query.getPageNum());
        result.setPageSize(query.getPageSize());
        int totalPages = (int) Math.ceil((double) total / query.getPageSize());
        result.setTotalPages(totalPages);
        return result;
    }

    @Override
    public PrescriptionDetailVO getPrescriptionDetail(Integer id) {
        PrescriptionDetailVO vo = prescriptionMapper.selectPrescriptionDetail(id);
        if (vo == null) {
            throw new BusinessException("处方不存在");
        }

        List<PrescriptionDetailVO.PrescriptionDrugDetailVO> drugs =
                prescriptionDetailMapper.selectDrugDetailByPrescriptionId(id);
        vo.setDrugs(drugs);
        return vo;
    }

    @Override
    public PageResult<ReportListVO> getReports(ReportQueryDTO query) {
        int offset = (query.getPageNum() - 1) * query.getPageSize();

        List<ReportListVO> list = medicalReportMapper.selectReportList(
                query.getPatientId(),
                query.getRequestType(),
                offset,
                query.getPageSize()
        );

        Long total = medicalReportMapper.countReportList(
                query.getPatientId(),
                query.getRequestType()
        );

        PageResult<ReportListVO> result = new PageResult<>();
        result.setRecords(list);
        result.setTotal(total);
        result.setPageNum(query.getPageNum());
        result.setPageSize(query.getPageSize());
        int totalPages = (int) Math.ceil((double) total / query.getPageSize());
        result.setTotalPages(totalPages);
        return result;
    }

    @Override
    public ReportDetailVO getReportDetail(Long id) {
        ReportDetailVO vo = medicalReportMapper.selectReportDetail(id);
        if (vo == null) {
            throw new BusinessException("报告不存在");
        }
        return vo;
    }

    @Override
    @Transactional
    public void markReportRead(Long id) {
        int affected = medicalReportMapper.markAsRead(id, LocalDateTime.now());
        if (affected == 0) {
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
    public QueueCountVO getQueueCount(Integer patientId) {
        // 获取当前患者今天已挂号但还没报到的数量
        Integer count = registerMapper.countTodayQueue(patientId, LocalDate.now());
        QueueCountVO vo = new QueueCountVO();
        vo.setQueueCount(count != null ? count : 0);
        return vo;
    }
}