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
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class DoctorServiceImpl implements DoctorService {
    @Autowired
    private EmployeeMapper employeeMapper;

    @Autowired
    private DepartmentMapper departmentMapper;
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
    private ChargeItemMapper chargeItemMapper;
    @Autowired
    private MedicalTechnologyMapper medicalTechnologyMapper;

    @Override
    public PageResult<DoctorPatientListVO> getPatients(DoctorPatientsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<Register> list = registerMapper.selectDoctorPatients(query.getDoctorId(), query.getVisitState());
        PageInfo<Register> pageInfo = new PageInfo<>(list);

        List<DoctorPatientListVO> voList = new ArrayList<>();
        for (Register r : list) {
            DoctorPatientListVO vo = new DoctorPatientListVO();
            vo.setRegisterId(r.getId());
            vo.setCaseNumber(r.getVisitNo());
            vo.setPatientName(r.getRealName());
            vo.setGender(r.getGender());
            vo.setAge(r.getAge());
            if (r.getVisitDate() != null) {
                vo.setRegistrationTime(r.getVisitDate().toString());
            }
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

    /**
     * 公共校验：挂号记录是否存在且未取消
     */
    private void checkRegisterCanOperate(Register register, String operationName) {
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }
        // 只拦截已取消状态，允许 FINISHED 等状态下继续操作
        if ("CANCELLED".equals(register.getVisitState())) {
            throw new BusinessException("该患者就诊已取消，无法" + operationName);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void saveMedicalRecord(MedicalRecordSaveRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        checkRegisterCanOperate(register, "保存病历");

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
        checkRegisterCanOperate(register, "开立检查");

        for (CheckRequestCreateDTO.CheckItemDTO item : request.getItems()) {
            CheckRequest check = new CheckRequest();
            check.setRegisterId(request.getRegisterId());
            check.setMedicalTechnologyId(item.getMedicalTechnologyId());
            check.setCheckInfo(item.getCheckInfo());
            check.setCheckPosition(item.getCheckPosition());
            checkRequestMapper.insert(check);

            MedicalTechnology tech = medicalTechnologyMapper.selectById(item.getMedicalTechnologyId());
            ChargeItem chargeItem = new ChargeItem();
            chargeItem.setSourceId(Long.valueOf(check.getId()));
            chargeItem.setSourceType("CHECK");
            chargeItem.setRegisterId(Long.valueOf(request.getRegisterId()));
            chargeItem.setItemName(tech != null ? tech.getTechName() : "Check");
            chargeItem.setItemType("CHECK");
            chargeItem.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
            chargeItem.setStatus("PENDING");
            chargeItemMapper.insert(chargeItem);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createInspectionRequest(InspectionRequestCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        checkRegisterCanOperate(register, "开立检验");

        for (InspectionRequestCreateDTO.InspectionItemDTO item : request.getItems()) {
            InspectionRequest inspection = new InspectionRequest();
            inspection.setRegisterId(request.getRegisterId());
            inspection.setMedicalTechnologyId(item.getMedicalTechnologyId());
            inspection.setInspectionInfo(item.getInspectionInfo());
            inspection.setInspectionPosition(item.getInspectionPosition());
            inspectionRequestMapper.insert(inspection);

            MedicalTechnology tech = medicalTechnologyMapper.selectById(item.getMedicalTechnologyId());
            ChargeItem chargeItem = new ChargeItem();
            chargeItem.setSourceId(Long.valueOf(inspection.getId()));
            chargeItem.setSourceType("INSPECTION");
            chargeItem.setRegisterId(Long.valueOf(request.getRegisterId()));
            chargeItem.setItemName(tech != null ? tech.getTechName() : "Inspection");
            chargeItem.setItemType("INSPECTION");
            chargeItem.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
            chargeItem.setStatus("PENDING");
            chargeItemMapper.insert(chargeItem);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void createDisposalRequest(DisposalRequestCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        checkRegisterCanOperate(register, "开立处置");

        for (DisposalRequestCreateDTO.DisposalItemDTO item : request.getItems()) {
            DisposalRequest disposal = new DisposalRequest();
            disposal.setRegisterId(request.getRegisterId());
            disposal.setMedicalTechnologyId(item.getMedicalTechnologyId());
            disposal.setDisposalInfo(item.getDisposalInfo());
            disposal.setDisposalPosition(item.getDisposalPosition());
            disposalRequestMapper.insert(disposal);

            MedicalTechnology tech = medicalTechnologyMapper.selectById(item.getMedicalTechnologyId());
            ChargeItem chargeItem = new ChargeItem();
            chargeItem.setSourceId(Long.valueOf(disposal.getId()));
            chargeItem.setSourceType("DISPOSAL");
            chargeItem.setRegisterId(Long.valueOf(request.getRegisterId()));
            chargeItem.setItemName(tech != null ? tech.getTechName() : "Disposal");
            chargeItem.setItemType("DISPOSAL");
            chargeItem.setAmount(tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
            chargeItem.setStatus("PENDING");
            chargeItemMapper.insert(chargeItem);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public Integer createPrescription(PrescriptionCreateDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        checkRegisterCanOperate(register, "开立处方");

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

            drugInfoMapper.updateStock(drug.getId(), drug.getStockNum() - item.getDrugNumber());
        }

        prescriptionDetailMapper.batchInsert(details);

        prescriptionMapper.updateStatusAndAmount(prescription.getId(), "CREATED", total);

        ChargeItem chargeItem = new ChargeItem();
        chargeItem.setSourceId(Long.valueOf(prescription.getId()));
        chargeItem.setSourceType("PRESCRIPTION");
        chargeItem.setRegisterId(Long.valueOf(request.getRegisterId()));
        chargeItem.setItemName("Drug");
        chargeItem.setItemType("DRUG");
        chargeItem.setAmount(total);
        chargeItem.setStatus("PENDING");
        chargeItemMapper.insert(chargeItem);

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
    @Transactional(rollbackFor = Exception.class)
    public void receiveDiagnosis(DiagnosisReceiveRequestDTO request) {
        Integer registerId = request.getRegisterId();
        if (registerId == null) {
            throw new BusinessException("挂号ID不能为空");
        }

        Register register = registerMapper.selectById(registerId);
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        // 1. 更新挂号状态为 FINISHED
        register.setVisitState("FINISHED");
        registerMapper.update(register);

        // 2. 保存或更新病历中的诊断信息
        MedicalRecord medicalRecord = medicalRecordMapper.selectByRegisterId(registerId);
        if (medicalRecord == null) {
            medicalRecord = new MedicalRecord();
            medicalRecord.setRegisterId(registerId);
            medicalRecord.setDoctorId(register.getEmployeeId());
        }

        if (request.getDiagnosis() != null) {
            medicalRecord.setDiagnosis(request.getDiagnosis());
        }
        if (request.getCure() != null) {
            medicalRecord.setCure(request.getCure());
        }

        if (medicalRecord.getId() == null) {
            medicalRecordMapper.insert(medicalRecord);
        } else {
            medicalRecordMapper.updateById(medicalRecord);
        }

        // 3. 保存疾病关联
        if (request.getDiseaseIds() != null && !request.getDiseaseIds().isEmpty()) {
            medicalRecordDiseaseMapper.deleteByMedicalRecordId(medicalRecord.getId());
            for (Integer diseaseId : request.getDiseaseIds()) {
                MedicalRecordDisease mrd = new MedicalRecordDisease();
                mrd.setMedicalRecordId(medicalRecord.getId());
                mrd.setDiseaseId(diseaseId);
                medicalRecordDiseaseMapper.insert(mrd);
            }
        }
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
        Employee emp = employeeMapper.selectById(doctorId);
        if (emp == null) return null;

        DoctorProfileVO vo = new DoctorProfileVO();
        vo.setId(emp.getId());
        vo.setRealname(emp.getRealname());
        vo.setTitleLevel(emp.getTitleLevel());
        vo.setPhone(emp.getPhone());
        vo.setRoleType(emp.getRoleType());
        vo.setDeptmentId(emp.getDeptmentId());
        vo.setDelmark(emp.getDelmark());
        if (emp.getCreateTime() != null) {
            vo.setCreateTime(emp.getCreateTime().toString());
        }

        if (emp.getDeptmentId() != null) {
            Department dept = departmentMapper.selectById(emp.getDeptmentId());
            if (dept != null) {
                vo.setDeptName(dept.getDeptName());
            }
        }
        return vo;
    }

    @Override
    public DoctorStatisticsVO getStatistics(Integer doctorId) {
        DoctorStatisticsVO vo = new DoctorStatisticsVO();
        vo.setTodayVisits(registerMapper.countTodayVisitsByDoctorId(doctorId));
        vo.setMonthVisits(registerMapper.countMonthVisitsByDoctorId(doctorId));
        vo.setTotalVisits(registerMapper.countTotalVisitsByDoctorId(doctorId));
        vo.setPendingCount(registerMapper.countPendingByDoctorId(doctorId));
        vo.setConsultingCount(registerMapper.countConsultingByDoctorId(doctorId));
        vo.setFinishedCount(registerMapper.countFinishedByDoctorId(doctorId));
        return vo;
    }

    @Override
    public CheckResultDetailVO getCheckResultDetail(Integer id) {
        CheckRequest check = checkRequestMapper.selectById(id);
        if (check == null) return null;

        CheckResultDetailVO vo = new CheckResultDetailVO();
        vo.setId(check.getId());
        vo.setCheckInfo(check.getCheckInfo());
        vo.setCheckPosition(check.getCheckPosition());
        vo.setCheckState(check.getCheckState());
        vo.setCheckResult(check.getCheckResult());
        vo.setCheckRemark(check.getCheckRemark());
        if (check.getCreationTime() != null) {
            vo.setCreateTime(check.getCreationTime().toString());
        }
        if (check.getCheckTime() != null) {
            vo.setCheckTime(check.getCheckTime().toString());
        }
        return vo;
    }

    @Override
    public MedicalRecordSaveRequestDTO getMedicalRecord(Integer registerId) {
        MedicalRecord record = medicalRecordMapper.selectByRegisterId(registerId);
        if (record == null) return null;

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
        CheckResultVO vo = new CheckResultVO();
        vo.setCheckRequests(checkRequestMapper.selectByRegisterId(registerId));
        vo.setInspectionRequests(inspectionRequestMapper.selectByRegisterId(registerId));
        vo.setDisposalRequests(disposalRequestMapper.selectByRegisterId(registerId));
        return vo;
    }

    @Override
    public List<Prescription> getPrescriptionsByRegisterId(Integer registerId) {
        return prescriptionMapper.selectByRegisterId(registerId);
    }

    @Override
    public DiagnosisConfirmRequestDTO getDiagnosis(Integer registerId) {
        MedicalRecord record = medicalRecordMapper.selectByRegisterId(registerId);
        if (record == null) return null;

        DiagnosisConfirmRequestDTO dto = new DiagnosisConfirmRequestDTO();
        dto.setRegisterId(record.getRegisterId());
        dto.setDiagnosis(record.getDiagnosis());
        dto.setCure(record.getCure());

        List<MedicalRecordDisease> diseases = medicalRecordDiseaseMapper.selectByMedicalRecordId(record.getId());
        if (diseases != null && !diseases.isEmpty()) {
            dto.setDiseaseIds(diseases.stream().map(MedicalRecordDisease::getDiseaseId).collect(Collectors.toList()));
        }
        return dto;
    }
}