package com.neuedu.his.controller;

import com.neuedu.his.mapper.DepartmentMapper;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.ChargeItem;
import com.neuedu.his.model.entity.Department;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.AdminService;
import com.neuedu.his.service.EmployeeService;
import com.neuedu.his.service.StatisticsService;
import com.neuedu.his.util.JwtUtil;
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
    private EmployeeService employeeService;

    @Autowired
    private StatisticsService statisticsService;
    @Autowired
    private DepartmentMapper departmentMapper;

    private Integer getOperatorId(String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            return null;
        }
        return JwtUtil.getUserIdFromToken(authHeader.substring(7));
    }

    // ========== Finance APIs ==========

    @PostMapping("/finance/charge")
    public void charge(@RequestBody @Valid ChargeRequestDTO request,
                       @RequestHeader("Authorization") String authHeader) {
        adminService.charge(request, getOperatorId(authHeader));
    }

    @PostMapping("/finance/refund")
    public void refund(@RequestBody @Valid RefundRequestDTO request,
                       @RequestHeader("Authorization") String authHeader) {
        adminService.refund(request, getOperatorId(authHeader));
    }

    @GetMapping("/finance/records")
    public PageResult<FinanceRecordVO> getFinanceRecords(@Valid FinanceRecordsQueryDTO query) {
        return adminService.getFinanceRecords(query);
    }

    @GetMapping("/finance/daily-summary")
    public DailySummaryVO getDailySummary(@Valid DailySummaryQueryDTO query) {
        return adminService.getDailySummary(query);
    }

    @GetMapping("/finance/pending-items")
    public List<ChargeItem> getPendingItems(@RequestParam Integer registerId) {
        return adminService.getPendingItems(registerId);
    }

    @GetMapping("/finance/paid-items")
    public List<ChargeItem> getPaidItems(@RequestParam Integer registerId) {
        return adminService.getPaidItems(registerId);
    }

    // ========== Drug APIs ==========

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
    public List<PrescriptionDispenseVO> getPendingDispense() {
        return adminService.getPendingDispense();
    }

    @GetMapping("/drug/pending-refund")
    public List<PrescriptionRefundVO> getPendingRefund() {
        return adminService.getPendingRefund();
    }

    // ========== Employee APIs ==========

    /**
     * Create employee profile (doctor/admin)
     */
    @PostMapping("/employee/create")
    public Integer createEmployee(@RequestBody @Valid EmployeeCreateRequestDTO request) {
        return employeeService.createEmployee(request);
    }

    /**
     * Get all employee list
     */
    @GetMapping("/employee/list")
    public List<EmployeeListItemVO> listEmployees() {
        return employeeService.listAllEmployees();
    }

    /**
     * Get all doctor list
     */
    @GetMapping("/employee/doctors")
    public List<EmployeeListItemVO> listDoctors() {
        return employeeService.listAllDoctors();
    }

    /**
     * Get all department list
     */
    @GetMapping("/department/list")
    public List<Department> listDepartments() {
        return departmentMapper.selectAll();
    }

    /**
     * Doctor statistics (visit count + revisit rate)
     */
    @GetMapping("/statistics/doctor")
    public List<DoctorStatsVO> getDoctorStats() {
        return statisticsService.getDoctorStats();
    }

    /**
     * Department statistics
     */
    @GetMapping("/statistics/dept")
    public List<DeptStatsVO> getDeptStats() {
        return statisticsService.getDeptStats();
    }
}
