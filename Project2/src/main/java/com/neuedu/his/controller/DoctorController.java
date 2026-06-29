package com.neuedu.his.controller;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.RegisterMapper;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.Register;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.DoctorService;
import com.neuedu.his.service.DashboardService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/doctor")
public class DoctorController {

    @Autowired
    private DoctorService doctorService;

    @Autowired
    private DashboardService dashboardService;

    @Autowired
    private RegisterMapper registerMapper;

    @GetMapping("/dashboard/summary")
    public DoctorDashboardSummaryVO getDashboardSummary(@RequestParam("doctorId") Integer doctorId) {
        return dashboardService.getDoctorSummary(doctorId);
    }

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

    @PutMapping("/patients/{registerId}/receive")
    public void receivePatient(@PathVariable("registerId") Integer registerId) {
        doctorService.receivePatient(registerId);
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

    @GetMapping("/check-results/{registerId}")
    public CheckResultVO getCheckResults(@PathVariable("registerId") Integer registerId) {
        return doctorService.getCheckResults(registerId);
    }
}
