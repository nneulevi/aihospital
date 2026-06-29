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
import java.util.ArrayList;
import java.util.List;

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

        for (CheckRequestCreateDTO.CheckItemDTO item : request.getItems()) {
            CheckRequest check = new CheckRequest();
            check.setRegisterId(request.getRegisterId());
            check.setMedicalTechnologyId(item.getMedicalTechnologyId());
            check.setCheckInfo(item.getCheckInfo());
            check.setCheckPosition(item.getCheckPosition());
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

        for (InspectionRequestCreateDTO.InspectionItemDTO item : request.getItems()) {
            InspectionRequest inspection = new InspectionRequest();
            inspection.setRegisterId(request.getRegisterId());
            inspection.setMedicalTechnologyId(item.getMedicalTechnologyId());
            inspection.setInspectionInfo(item.getInspectionInfo());
            inspection.setInspectionPosition(item.getInspectionPosition());
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

        for (DisposalRequestCreateDTO.DisposalItemDTO item : request.getItems()) {
            DisposalRequest disposal = new DisposalRequest();
            disposal.setRegisterId(request.getRegisterId());
            disposal.setMedicalTechnologyId(item.getMedicalTechnologyId());
            disposal.setDisposalInfo(item.getDisposalInfo());
            disposal.setDisposalPosition(item.getDisposalPosition());
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

            drugInfoMapper.updateStock(drug.getId(), drug.getStockNum() - item.getDrugNumber());
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


}