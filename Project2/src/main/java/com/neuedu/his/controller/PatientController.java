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
}
