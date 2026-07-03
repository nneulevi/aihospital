package com.neuedu.his.controller;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.RegisterMapper;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.Prescription;
import com.neuedu.his.model.entity.Register;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.DoctorService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/doctor")
public class DoctorController {

    @Autowired
    private DoctorService doctorService;

    @Autowired
    private RegisterMapper registerMapper;

    @GetMapping("/patients")
    public PageResult<DoctorPatientListVO> getPatients(@Valid DoctorPatientsQueryDTO query) {
        return doctorService.getPatients(query);
    }

    @GetMapping("/patients/{registerId}")
    public DoctorPatientListVO getPatientDetail(@PathVariable("registerId") Integer registerId) {
        Register register = registerMapper.selectVisitDetail(registerId);
        if (register == null) {
            throw new BusinessException("患者就诊记录不存在");
        }

        DoctorPatientListVO vo = new DoctorPatientListVO();
        vo.setRegisterId(register.getId());
        vo.setCaseNumber(register.getVisitNo());
        vo.setRegistrationTime(register.getVisitDate() != null ? register.getVisitDate().toString() : "");
        vo.setNoon(register.getNoon());
        return vo;
    }

    @PostMapping("/medical-record")
    public void saveMedicalRecord(@RequestBody @Valid MedicalRecordSaveRequestDTO request) {
        doctorService.saveMedicalRecord(request);
    }

    @PostMapping("/check-request")
    public void createCheckRequest(@RequestBody @Valid CheckRequestCreateDTO request) {
        doctorService.createCheckRequest(request);
    }

    @PostMapping("/inspection-request")
    public void createInspectionRequest(@RequestBody @Valid InspectionRequestCreateDTO request) {
        doctorService.createInspectionRequest(request);
    }

    @PostMapping("/disposal-request")
    public void createDisposalRequest(@RequestBody @Valid DisposalRequestCreateDTO request) {
        doctorService.createDisposalRequest(request);
    }

    @PostMapping("/prescription")
    public Integer createPrescription(@RequestBody @Valid PrescriptionCreateDTO request) {
        return doctorService.createPrescription(request);
    }

    @PutMapping("/diagnosis/confirm")
    public void confirmDiagnosis(@RequestBody @Valid DiagnosisConfirmRequestDTO request) {
        doctorService.confirmDiagnosis(request);
    }

    /**
     * 医生确诊 - 保存诊断内容并结束就诊
     */
    @PutMapping("/diagnosis/receive")
    public void receiveDiagnosis(@RequestBody DiagnosisReceiveRequestDTO request) {
        doctorService.receiveDiagnosis(request);
    }

    @GetMapping("/check-results/{registerId}")
    public CheckResultVO getCheckResults(@PathVariable("registerId") Integer registerId) {
        return doctorService.getCheckResults(registerId);
    }
    @GetMapping("/profile")
    public DoctorProfileVO getProfile(@RequestParam Integer doctorId) {
        return doctorService.getProfile(doctorId);
    }

    @GetMapping("/statistics")
    public DoctorStatisticsVO getStatistics(@RequestParam Integer doctorId) {
        return doctorService.getStatistics(doctorId);
    }

    @GetMapping("/check-result/{id}")
    public CheckResultDetailVO getCheckResultDetail(@PathVariable Integer id) {
        return doctorService.getCheckResultDetail(id);
    }

    @GetMapping("/medical-record/{registerId}")
    public MedicalRecordSaveRequestDTO getMedicalRecord(@PathVariable("registerId") Integer registerId) {
        return doctorService.getMedicalRecord(registerId);
    }

    @GetMapping("/orders/{registerId}")
    public CheckResultVO getOrders(@PathVariable("registerId") Integer registerId) {
        return doctorService.getOrders(registerId);
    }

    @GetMapping("/prescriptions/{registerId}")
    public List<Prescription> getPrescriptionsByRegisterId(@PathVariable("registerId") Integer registerId) {
        return doctorService.getPrescriptionsByRegisterId(registerId);
    }

    @GetMapping("/diagnosis/{registerId}")
    public DiagnosisConfirmRequestDTO getDiagnosis(@PathVariable("registerId") Integer registerId) {
        return doctorService.getDiagnosis(registerId);
    }
}