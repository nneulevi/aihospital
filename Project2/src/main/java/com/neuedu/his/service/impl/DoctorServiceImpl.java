package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.*;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.DoctorService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.Period;
import java.util.ArrayList;
import java.util.List;

@Service
public class DoctorServiceImpl implements DoctorService {

    @Autowired
    private RegisterMapper registerMapper;
    @Autowired
    private MedicalRecordMapper medicalRecordMapper;
    @Autowired
    private MedicalRecordDiseaseMapper medicalRecordDiseaseMapper;
    @Autowired
    private CheckRequestMapper checkRequestMapper;
    @Autowired
    private InspectionRequestMapper inspectionRequestMapper;
    @Autowired
    private DisposalRequestMapper disposalRequestMapper;
    @Autowired
    private PrescriptionMapper prescriptionMapper;
    @Autowired
    private PrescriptionDetailMapper prescriptionDetailMapper;
    @Autowired
    private DrugInfoMapper drugInfoMapper;
    @Autowired
    private DiseaseMapper diseaseMapper;
    @Autowired
    private MedicalTechnologyMapper medicalTechnologyMapper;
    @Autowired
    private EmployeeMapper employeeMapper;
    @Autowired
    private DepartmentMapper departmentMapper;
    @Autowired
    private DashboardMapper dashboardMapper;

    @Override
    public PageResult<DoctorPatientListVO> getPatients(DoctorPatientsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<Register> list = registerMapper.selectDoctorPatients(
                query.getDoctorId(),
                query.getVisitState(),
                query.getVisitDate(),
                query.getNoon()
        );
        PageInfo<Register> pageInfo = new PageInfo<>(list);

        List<DoctorPatientListVO> voList = new ArrayList<>();
        for (Register r : list) {
            DoctorPatientListVO vo = new DoctorPatientListVO();
            vo.setRegisterId(r.getId());
            vo.setCaseNumber(r.getCaseNumber() != null ? r.getCaseNumber() : r.getVisitNo());
            vo.setPatientName(r.getRealName());
            vo.setGender(r.getGender());
            vo.setAge(r.getBirthdate() == null ? null : Period.between(r.getBirthdate(), LocalDate.now()).getYears());
            vo.setRegistrationTime(r.getCreateTime() == null ? null : r.getCreateTime().toString());
            vo.setNoon(r.getNoon());
            vo.setVisitState(r.getVisitState());
            voList.add(vo);
        }

        PageResult<DoctorPatientListVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void receivePatient(Integer registerId) {
        Register register = registerMapper.selectById(registerId);
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }
        if (!"REGISTERED".equals(register.getVisitState())
                && !"CHECKED_IN".equals(register.getVisitState())
                && !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("当前挂号状态无法接诊: " + register.getVisitState());
        }
        if (!"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            registerMapper.updateState(registerId, "DOCTOR_RECEIVED");
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void returnToWaiting(Integer registerId) {
        Register register = registerMapper.selectById(registerId);
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }
        if (!"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("仅已接诊且未确诊的患者可以退回候诊");
        }
        registerMapper.updateState(registerId, "REGISTERED");
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void saveMedicalRecord(MedicalRecordSaveRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null || !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("该患者未接诊，无法保存病历");
        }

        MedicalRecord exist = medicalRecordMapper.selectByRegisterId(request.getRegisterId());
        if (exist != null) {
            exist.setReadme(request.getReadme());
            exist.setPresent(request.getPresent());
            exist.setPresentTreat(request.getPresentTreat());
            exist.setHistory(request.getHistory());
            exist.setAllergy(request.getAllergy());
            exist.setPhysique(request.getPhysique());
            exist.setProposal(request.getProposal());
            exist.setCareful(request.getCareful());
            exist.setDiagnosis(request.getDiagnosis());
            medicalRecordMapper.updateById(exist);
        } else {
            MedicalRecord record = new MedicalRecord();
            record.setRegisterId(request.getRegisterId());
            record.setDoctorId(register.getEmployeeId());
            record.setReadme(request.getReadme());
            record.setPresent(request.getPresent());
            record.setPresentTreat(request.getPresentTreat());
            record.setHistory(request.getHistory());
            record.setAllergy(request.getAllergy());
            record.setPhysique(request.getPhysique());
            record.setProposal(request.getProposal());
            record.setCareful(request.getCareful());
            record.setDiagnosis(request.getDiagnosis());
            record.setRecordStatus("DRAFT");
            medicalRecordMapper.insert(record);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createCheckRequest(CheckRequestCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null || !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("该患者未接诊，无法开立检查");
        }
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new BusinessException("检查项目不能为空");
        }

        for (CheckRequestCreateDTO.CheckItemDTO item : request.getItems()) {
            requireItem(item != null, "检查项目不能为空");
            requireText(item.getCheckInfo(), "检查项目名称不能为空");
            requireText(item.getCheckPosition(), "检查部位不能为空");
            CheckRequest check = new CheckRequest();
            check.setRegisterId(request.getRegisterId());
            check.setMedicalTechnologyId(item.getMedicalTechnologyId());
            check.setCheckInfo(item.getCheckInfo().trim());
            check.setCheckPosition(item.getCheckPosition().trim());
            checkRequestMapper.insert(check);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createInspectionRequest(InspectionRequestCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null || !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("该患者未接诊，无法开立检验");
        }
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new BusinessException("检验项目不能为空");
        }

        for (InspectionRequestCreateDTO.InspectionItemDTO item : request.getItems()) {
            requireItem(item != null, "检验项目不能为空");
            requireText(item.getInspectionInfo(), "检验项目名称不能为空");
            requireText(item.getInspectionPosition(), "检验样本不能为空");
            InspectionRequest inspection = new InspectionRequest();
            inspection.setRegisterId(request.getRegisterId());
            inspection.setMedicalTechnologyId(item.getMedicalTechnologyId());
            inspection.setInspectionInfo(item.getInspectionInfo().trim());
            inspection.setInspectionPosition(item.getInspectionPosition().trim());
            inspectionRequestMapper.insert(inspection);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createDisposalRequest(DisposalRequestCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null || !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("该患者未接诊，无法开立处置");
        }
        if (request.getItems() == null || request.getItems().isEmpty()) {
            throw new BusinessException("处置项目不能为空");
        }

        for (DisposalRequestCreateDTO.DisposalItemDTO item : request.getItems()) {
            requireItem(item != null, "处置项目不能为空");
            requireText(item.getDisposalInfo(), "处置项目名称不能为空");
            requireText(item.getDisposalPosition(), "处置部位不能为空");
            DisposalRequest disposal = new DisposalRequest();
            disposal.setRegisterId(request.getRegisterId());
            disposal.setMedicalTechnologyId(item.getMedicalTechnologyId());
            disposal.setDisposalInfo(item.getDisposalInfo().trim());
            disposal.setDisposalPosition(item.getDisposalPosition().trim());
            disposalRequestMapper.insert(disposal);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Integer createPrescription(PrescriptionCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null || !"DOCTOR_RECEIVED".equals(register.getVisitState())) {
            throw new BusinessException("该患者未接诊，无法开立处方");
        }

        Prescription prescription = new Prescription();
        prescription.setRegisterId(request.getRegisterId());
        prescription.setDoctorId(request.getDoctorId());
        prescription.setPrescriptionNo("P" + System.currentTimeMillis());
        prescription.setPrescriptionStatus("CREATED");
        prescription.setTotalAmount(BigDecimal.ZERO);
        prescriptionMapper.insert(prescription);

        BigDecimal total = BigDecimal.ZERO;
        List<PrescriptionDetail> details = new ArrayList<>();

        for (PrescriptionCreateDTO.PrescriptionItemDTO item : request.getItems()) {
            DrugInfo drug = drugInfoMapper.selectById(item.getDrugId());
            if (drug == null || drug.getStockNum() < item.getDrugNumber()) {
                throw new BusinessException("药品【" + (drug != null ? drug.getDrugName() : "未知") + "】库存不足");
            }

            PrescriptionDetail detail = new PrescriptionDetail();
            detail.setPrescriptionId(prescription.getId());
            detail.setDrugId(item.getDrugId());
            detail.setUsageRoute(item.getUsageRoute());
            detail.setFrequency(item.getFrequency());
            detail.setSingleDose(item.getSingleDose());
            detail.setUseDays(item.getUseDays());
            detail.setDrugNumber(item.getDrugNumber());
            details.add(detail);

            total = total.add(drug.getDrugPrice().multiply(new BigDecimal(item.getDrugNumber())));

        }

        prescriptionDetailMapper.batchInsert(details);

        prescriptionMapper.updateStatusAndAmount(prescription.getId(), "CREATED", total);

        return prescription.getId();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void confirmDiagnosis(DiagnosisConfirmRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        MedicalRecord record = medicalRecordMapper.selectByRegisterId(request.getRegisterId());
        if (record == null) {
            throw new BusinessException("病历不存在，请先填写病历");
        }

        record.setDiagnosis(request.getDiagnosis());
        record.setCure(request.getCure());
        record.setRecordStatus("SIGNED");
        medicalRecordMapper.updateById(record);

        if (request.getDiseaseIds() != null) {
            medicalRecordDiseaseMapper.deleteByMedicalRecordId(record.getId());
            for (Integer diseaseId : request.getDiseaseIds()) {
                MedicalRecordDisease mrd = new MedicalRecordDisease();
                mrd.setMedicalRecordId(record.getId());
                mrd.setDiseaseId(diseaseId);
                medicalRecordDiseaseMapper.insert(mrd);
            }
        }

        registerMapper.updateState(request.getRegisterId(), "DIAGNOSIS_DONE");
    }

    @Override
    public MedicalRecordSaveRequestDTO getMedicalRecord(Integer registerId) {
        MedicalRecord record = medicalRecordMapper.selectByRegisterId(registerId);
        if (record == null) {
            return null;
        }

        MedicalRecordSaveRequestDTO dto = new MedicalRecordSaveRequestDTO();
        dto.setRegisterId(record.getRegisterId());
        dto.setReadme(record.getReadme());
        dto.setPresent(record.getPresent());
        dto.setPresentTreat(record.getPresentTreat());
        dto.setHistory(record.getHistory());
        dto.setAllergy(record.getAllergy());
        dto.setPhysique(record.getPhysique());
        dto.setProposal(record.getProposal());
        dto.setCareful(record.getCareful());
        dto.setDiagnosis(record.getDiagnosis());
        return dto;
    }

    @Override
    public CheckResultVO getOrders(Integer registerId) {
        return getCheckResults(registerId);
    }

    @Override
    public List<Prescription> getPrescriptionsByRegisterId(Integer registerId) {
        return prescriptionMapper.selectByRegisterId(registerId);
    }

    @Override
    public DiagnosisConfirmRequestDTO getDiagnosis(Integer registerId) {
        MedicalRecord record = medicalRecordMapper.selectByRegisterId(registerId);
        if (record == null) {
            return null;
        }

        DiagnosisConfirmRequestDTO dto = new DiagnosisConfirmRequestDTO();
        dto.setRegisterId(registerId);
        dto.setDiagnosis(record.getDiagnosis());
        dto.setCure(record.getCure());
        List<Integer> diseaseIds = new ArrayList<>();
        for (MedicalRecordDisease disease : medicalRecordDiseaseMapper.selectByMedicalRecordId(record.getId())) {
            diseaseIds.add(disease.getDiseaseId());
        }
        dto.setDiseaseIds(diseaseIds);
        return dto;
    }

    @Override
    public CheckResultVO getCheckResults(Integer registerId) {
        CheckResultVO vo = new CheckResultVO();
        vo.setCheckRequests(checkRequestMapper.selectByRegisterId(registerId));
        vo.setInspectionRequests(inspectionRequestMapper.selectByRegisterId(registerId));
        vo.setDisposalRequests(disposalRequestMapper.selectByRegisterId(registerId));
        return vo;
    }

    @Override
    public DoctorProfileVO getProfile(Integer doctorId) {
        Employee employee = employeeMapper.selectById(doctorId);
        if (employee == null || !"DOCTOR".equals(employee.getRoleType())) {
            throw new BusinessException("医生不存在");
        }
        Department department = employee.getDeptmentId() == null ? null : departmentMapper.selectById(employee.getDeptmentId());
        DoctorProfileVO vo = new DoctorProfileVO();
        vo.setDoctorId(employee.getId());
        vo.setDoctorName(employee.getRealname());
        vo.setTitleLevel(employee.getTitleLevel());
        vo.setPhone(employee.getPhone());
        vo.setRoleType(employee.getRoleType());
        vo.setDeptId(employee.getDeptmentId());
        vo.setDeptName(department == null ? "未分配科室" : department.getDeptName());
        vo.setActive(Boolean.TRUE.equals(employee.getDelmark()));
        vo.setCreateTime(employee.getCreateTime());
        return vo;
    }

    @Override
    public DoctorStatisticsVO getStatistics(Integer doctorId) {
        getProfile(doctorId);
        DoctorStatisticsVO vo = new DoctorStatisticsVO();
        vo.setTodayVisits(defaultLong(registerMapper.countDoctorTodayVisits(doctorId)));
        vo.setMonthVisits(defaultLong(registerMapper.countDoctorMonthVisits(doctorId)));
        vo.setTotalVisits(defaultLong(registerMapper.countDoctorTotalVisits(doctorId)));
        vo.setPendingCount(defaultLong(dashboardMapper.countDoctorPending(doctorId)));
        vo.setConsultingCount(defaultLong(dashboardMapper.countDoctorConsulting(doctorId)));
        vo.setFinishedCount(defaultLong(dashboardMapper.countDoctorFinishedToday(doctorId)));
        vo.setPendingCheckCount(defaultLong(dashboardMapper.countDoctorPendingChecks(doctorId)));
        return vo;
    }

    @Override
    public CheckResultDetailVO getCheckResultDetail(Integer itemId) {
        CheckRequest check = checkRequestMapper.selectById(itemId);
        if (check == null) {
            throw new BusinessException("检查结果不存在");
        }
        MedicalTechnology technology = medicalTechnologyMapper.selectById(check.getMedicalTechnologyId());
        CheckResultDetailVO vo = new CheckResultDetailVO();
        vo.setId(check.getId());
        vo.setRegisterId(check.getRegisterId());
        vo.setItemType("CHECK");
        vo.setItemName(technology == null ? "检查项目" : technology.getTechName());
        vo.setItemPosition(check.getCheckPosition());
        vo.setResult(check.getCheckResult());
        vo.setState(check.getCheckState());
        vo.setStateName(formatRequestState(check.getCheckState()));
        vo.setReportTime(check.getCheckTime());
        return vo;
    }

    private Long defaultLong(Long value) {
        return value == null ? 0L : value;
    }

    private void requireItem(boolean condition, String message) {
        if (!condition) {
            throw new BusinessException(message);
        }
    }

    private void requireText(String value, String message) {
        if (value == null || value.trim().isEmpty()) {
            throw new BusinessException(message);
        }
    }

    private String formatRequestState(String state) {
        if ("CREATED".equals(state)) return "待缴费";
        if ("CHARGED".equals(state)) return "已缴费";
        if ("EXECUTING".equals(state)) return "执行中";
        if ("COMPLETED".equals(state)) return "已完成";
        if ("REFUNDED".equals(state)) return "已退费";
        if ("CANCELLED".equals(state)) return "已取消";
        return state;
    }
}
