package com.neuedu.his.controller;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.PatientService;
import com.neuedu.his.service.DashboardService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/patient")
public class PatientController {

    @Autowired
    private PatientService patientService;

    @Autowired
    private DashboardService dashboardService;

    @GetMapping("/dashboard/summary")
    public PatientDashboardSummaryVO getDashboardSummary(@RequestParam("patientId") Integer patientId) {
        return dashboardService.getPatientSummary(patientId);
    }

    @PostMapping("/send-code")
    public void sendCode(@RequestBody @Valid SendCodeRequestDTO request) {
        patientService.sendCode(request);
    }

    @PostMapping("/auth/register")
    public LoginResponseVO authRegister(@RequestBody @Valid PatientAuthRegisterRequestDTO request) {
        return patientService.authRegister(request);
    }

    @PostMapping("/logout")
    public void logout() {
        patientService.logout();
    }

    @PostMapping("/switch")
    public String switchPatient(@RequestParam("patientId") Integer patientId) {
        return patientService.switchPatient(patientId);
    }

    @GetMapping("/list")
    public List<PatientListVO> list() {
        return patientService.listPatients();
    }

    @PostMapping("/register")
    public Integer register(@RequestBody @Valid PatientRegisterRequestDTO request) {
        return patientService.register(request);
    }

    @PutMapping("/register/cancel")
    public void cancelRegister(@RequestBody @Valid RegisterCancelRequestDTO request) {
        patientService.cancelRegister(request);
    }

    @GetMapping("/records")
    public PageResult<PatientRecordListVO> getRecords(@Valid PatientRecordsQueryDTO query) {
        return patientService.getRecords(query);
    }

    @GetMapping("/records/{id}")
    public PatientRecordListVO getRecordDetail(@PathVariable("id") Integer registerId) {
        return patientService.getRecordDetail(registerId);
    }

    @GetMapping("/doctors")
    public PageResult<DoctorListVO> getDoctors(@Valid DoctorListQueryDTO query) {
        return patientService.getDoctors(query);
    }

    @GetMapping("/orders")
    public PageResult<OrderListVO> getOrders(@Valid PatientOrdersQueryDTO query) {
        return patientService.getOrders(query);
    }

    @GetMapping("/department/list")
    public List<PatientDepartmentVO> getDepartments() {
        return patientService.getDepartments();
    }

    @GetMapping("/register/today")
    public PatientTodayRegisterVO getTodayRegister(@RequestParam("patientId") Integer patientId) {
        return patientService.getTodayRegister(patientId);
    }

    @PostMapping("/checkin/submit")
    public PatientCheckinResultVO submitCheckin(@RequestParam("patientId") Integer patientId,
                                                @RequestParam(value = "registerId", required = false) Integer registerId) {
        return patientService.submitCheckin(patientId, registerId);
    }

    @GetMapping("/queue/status")
    public PatientQueueStatusVO getQueueStatus(@RequestParam("patientId") Integer patientId,
                                               @RequestParam(value = "registerId", required = false) Integer registerId) {
        return patientService.getQueueStatus(patientId, registerId);
    }

    @GetMapping("/queue/depts")
    public List<DeptQueueVO> getQueueDepts(@RequestParam("patientId") Integer patientId) {
        return patientService.getQueueDepts(patientId);
    }

    @GetMapping("/queue/count")
    public QueueCountVO getQueueCount(@RequestParam("patientId") Integer patientId) {
        return patientService.getQueueCount(patientId);
    }

    @GetMapping("/medical-technology/inspection")
    public List<PatientMedicalTechnologyVO> getInspectionTechnologies(@RequestParam(value = "deptId", required = false) Integer deptId) {
        return patientService.getMedicalTechnologies("INSPECTION", deptId);
    }

    @GetMapping("/medical-technology/check")
    public List<PatientMedicalTechnologyVO> getCheckTechnologies(@RequestParam(value = "deptId", required = false) Integer deptId) {
        return patientService.getMedicalTechnologies("CHECK", deptId);
    }

    @PostMapping("/inspection-request")
    public void createInspectionRequest(@RequestBody @Valid PatientInspectionRequestDTO request) {
        patientService.createInspectionRequest(request);
    }

    @PostMapping("/check-request")
    public void createCheckRequest(@RequestBody @Valid PatientCheckRequestDTO request) {
        patientService.createCheckRequest(request);
    }

    @GetMapping("/inspection-requests")
    public PageResult<PatientMedicalRequestVO> getInspectionRequests(@RequestParam("patientId") Integer patientId,
                                                                     @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
                                                                     @RequestParam(value = "pageSize", defaultValue = "20") Integer pageSize) {
        return patientService.getInspectionRequests(patientId, pageNum, pageSize);
    }

    @GetMapping("/check-requests")
    public PageResult<PatientMedicalRequestVO> getCheckRequests(@RequestParam("patientId") Integer patientId,
                                                                @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
                                                                @RequestParam(value = "pageSize", defaultValue = "20") Integer pageSize) {
        return patientService.getCheckRequests(patientId, pageNum, pageSize);
    }

    @GetMapping("/prescriptions")
    public PageResult<PatientPrescriptionVO> getPrescriptions(@RequestParam("patientId") Integer patientId,
                                                              @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
                                                              @RequestParam(value = "pageSize", defaultValue = "20") Integer pageSize) {
        return patientService.getPrescriptions(patientId, pageNum, pageSize);
    }

    @GetMapping("/prescriptions/{id}")
    public PrescriptionDetailVO getPrescriptionDetail(@PathVariable("id") Integer prescriptionId) {
        return patientService.getPrescriptionDetail(prescriptionId);
    }

    @GetMapping("/reports")
    public PageResult<PatientReportVO> getReports(@RequestParam("patientId") Integer patientId,
                                                  @RequestParam(value = "pageNum", defaultValue = "1") Integer pageNum,
                                                  @RequestParam(value = "pageSize", defaultValue = "20") Integer pageSize) {
        return patientService.getReports(patientId, pageNum, pageSize);
    }

    @GetMapping("/reports/{id}")
    public ReportDetailVO getReportDetail(@PathVariable("id") String reportId) {
        return patientService.getReportDetail(reportId);
    }

    @PutMapping("/reports/{id}/read")
    public void markReportRead(@PathVariable("id") String reportId) {
        patientService.markReportRead(reportId);
    }

    @GetMapping("/current")
    public PatientCurrentVO getCurrentPatient(@RequestParam("patientId") Integer patientId) {
        return patientService.getCurrentPatient(patientId);
    }

    @PutMapping("/inspection-request/book")
    public void bookInspectionRequest(@RequestBody @Valid BookRequestDTO request) {
        patientService.bookInspectionRequest(request);
    }

    @PutMapping("/check-request/book")
    public void bookCheckRequest(@RequestBody @Valid BookRequestDTO request) {
        patientService.bookCheckRequest(request);
    }
}
