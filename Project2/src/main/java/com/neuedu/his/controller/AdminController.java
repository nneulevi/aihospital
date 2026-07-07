package com.neuedu.his.controller;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.AdminService;
import com.neuedu.his.service.DashboardService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/admin")
public class AdminController {

    @Autowired
    private AdminService adminService;

    @Autowired
    private DashboardService dashboardService;

    @GetMapping("/dashboard/summary")
    public AdminDashboardSummaryVO getDashboardSummary() {
        return dashboardService.getAdminSummary();
    }

    @PostMapping("/staff")
    public StaffCreateResponseVO createStaff(@RequestBody @Valid StaffCreateRequestDTO request) {
        return adminService.createStaff(request);
    }

    @PostMapping("/employee/create")
    public Integer createEmployee(@RequestBody @Valid StaffCreateRequestDTO request) {
        return adminService.createEmployee(request);
    }

    @GetMapping("/employee/list")
    public List<EmployeeListItemVO> listEmployees() {
        return adminService.listEmployees(null);
    }

    @GetMapping("/employee/doctors")
    public List<EmployeeListItemVO> listDoctors() {
        return adminService.listEmployees("DOCTOR");
    }

    @GetMapping("/department/list")
    public List<PatientDepartmentVO> listDepartments() {
        return adminService.listDepartments();
    }

    @GetMapping("/stats/doctors")
    public List<DoctorStatsVO> getDoctorStats() {
        return adminService.getDoctorStats();
    }

    @GetMapping("/statistics/doctor")
    public List<DoctorStatsVO> getDoctorStatistics() {
        return adminService.getDoctorStats();
    }

    @GetMapping("/stats/departments")
    public List<DepartmentStatsVO> getDepartmentStats() {
        return adminService.getDepartmentStats();
    }

    @GetMapping("/statistics/dept")
    public List<DepartmentStatsVO> getDepartmentStatistics() {
        return adminService.getDepartmentStats();
    }

    @PostMapping("/finance/charge")
    public void charge(@RequestBody @Valid ChargeRequestDTO request) {
        adminService.charge(request);
    }

    @PostMapping("/finance/refund")
    public void refund(@RequestBody @Valid RefundRequestDTO request) {
        adminService.refund(request);
    }

    @GetMapping("/finance/records")
    public PageResult<FinanceRecordVO> getFinanceRecords(@Valid FinanceRecordsQueryDTO query) {
        return adminService.getFinanceRecords(query);
    }

    @GetMapping("/finance/pending-items")
    public List<ChargeItemVO> getPendingItems(@RequestParam("registerId") Integer registerId) {
        return adminService.getPendingItems(registerId);
    }

    @GetMapping("/finance/paid-items")
    public List<ChargeItemVO> getPaidItems(@RequestParam("registerId") Integer registerId) {
        return adminService.getPaidItems(registerId);
    }

    @GetMapping("/finance/daily-summary")
    public DailySummaryVO getDailySummary(@Valid DailySummaryQueryDTO query) {
        return adminService.getDailySummary(query);
    }

    @PostMapping("/drug/dispense")
    public void dispense(@RequestBody @Valid DispenseRequestDTO request) {
        adminService.dispense(request);
    }

    @PostMapping("/drug/refund")
    public void drugRefund(@RequestBody @Valid DrugRefundRequestDTO request) {
        adminService.drugRefund(request);
    }

    @GetMapping("/drug/inventory")
    public PageResult<DrugInventoryVO> getDrugInventory(@Valid DrugInventoryQueryDTO query) {
        return adminService.getDrugInventory(query);
    }

    @GetMapping("/drug/pending-dispense")
    public List<PrescriptionWorkItemVO> getPendingDispense() {
        return adminService.getPendingDispense();
    }

    @GetMapping("/drug/pending-refund")
    public List<PrescriptionWorkItemVO> getPendingRefund() {
        return adminService.getPendingRefund();
    }
}
