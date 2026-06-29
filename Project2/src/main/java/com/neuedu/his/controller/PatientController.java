package com.neuedu.his.controller;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.PatientService;
import com.neuedu.his.util.JwtUtil;
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
    private JwtUtil jwtUtil;

    // ==================== 原有接口 ====================

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

    // ==================== 新增接口 ====================

    /**
     * 科室列表（患者端）
     */
    @GetMapping("/department/list")
    public List<DeptListVO> listDepartments() {
        return patientService.listDepartments();
    }

    /**
     * 今日可报到列表
     */
    @GetMapping("/register/today")
    public List<TodayRegisterVO> getTodayRegisters(@RequestParam Integer patientId) {
        return patientService.getTodayRegisters(patientId);
    }

    /**
     * 报到提交
     */
    @PostMapping("/checkin/submit")
    public CheckinResultVO submitCheckin(@RequestBody @Valid CheckinRequestDTO request) {
        return patientService.submitCheckin(request);
    }

    /**
     * 候诊状态
     */
    @GetMapping("/queue/status")
    public QueueStatusVO getQueueStatus(@RequestParam Integer registerId) {
        return patientService.getQueueStatus(registerId);
    }

    /**
     * 候诊科室列表
     */
    @GetMapping("/queue/depts")
    public List<DeptQueueVO> getQueueDepts(@RequestParam Integer patientId) {
        return patientService.getQueueDepts(patientId);
    }

    /**
     * 候诊角标
     */
    @GetMapping("/queue/count")
    public QueueCountVO getQueueCount(@RequestParam Integer patientId) {
        return patientService.getQueueCount(patientId);
    }

    /**
     * 检验项目列表
     */
    @GetMapping("/medical-technology/inspection")
    public List<MedicalTechVO> getInspectionList() {
        return patientService.getInspectionList();
    }

    /**
     * 检查项目列表
     */
    @GetMapping("/medical-technology/check")
    public List<MedicalTechVO> getCheckList() {
        return patientService.getCheckList();
    }

    /**
     * 检验预约提交（患者端）
     */
    @PostMapping("/inspection-request")
    public void createInspectionRequest(@RequestBody @Valid PatientInspectionRequestDTO request) {
        patientService.createInspectionRequest(request);
    }

    /**
     * 检查预约提交（患者端）
     */
    @PostMapping("/check-request")
    public void createCheckRequest(@RequestBody @Valid PatientCheckRequestDTO request) {
        patientService.createCheckRequest(request);
    }

    /**
     * 处方列表
     */
    @GetMapping("/prescriptions")
    public PageResult<PrescriptionListVO> getPrescriptions(@Valid PrescriptionQueryDTO query) {
        return patientService.getPrescriptions(query);
    }

    /**
     * 处方详情
     */
    @GetMapping("/prescriptions/{id}")
    public PrescriptionDetailVO getPrescriptionDetail(@PathVariable Integer id) {
        return patientService.getPrescriptionDetail(id);
    }

    /**
     * 报告列表
     */
    @GetMapping("/reports")
    public PageResult<ReportListVO> getReports(@Valid ReportQueryDTO query) {
        return patientService.getReports(query);
    }

    /**
     * 报告详情
     */
    @GetMapping("/reports/{id}")
    public ReportDetailVO getReportDetail(@PathVariable Long id) {
        return patientService.getReportDetail(id);
    }

    /**
     * 标记报告已读
     */
    @PutMapping("/reports/{id}/read")
    public void markReportRead(@PathVariable Long id) {
        patientService.markReportRead(id);
    }

    /**
     * 当前患者信息
     */
    @GetMapping("/current")
    public PatientCurrentVO getCurrentPatient(@RequestHeader("Authorization") String token) {
        Integer patientId = jwtUtil.getUserIdFromToken(token.replace("Bearer ", ""));
        return patientService.getCurrentPatient(patientId);
    }
}