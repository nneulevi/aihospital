package com.neuedu.his.controller;

import com.neuedu.his.mapper.DepartmentMapper;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.Department;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.AdminService;
import com.neuedu.his.service.EmployeeService;
import com.neuedu.his.service.StatisticsService;
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
    // ========== 原有接口 ==========

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

    // ========== 新增接口 ==========

    /**
     * 创建职员档案（医生/管理员）
     */
    @PostMapping("/employee/create")
    public Integer createEmployee(@RequestBody @Valid EmployeeCreateRequestDTO request) {
        return employeeService.createEmployee(request);
    }

    /**
     * 获取所有职员列表
     */
    @GetMapping("/employee/list")
    public List<EmployeeListItemVO> listEmployees() {
        return employeeService.listAllEmployees();
    }

    /**
     * 获取所有医生列表
     */
    @GetMapping("/employee/doctors")
    public List<EmployeeListItemVO> listDoctors() {
        return employeeService.listAllDoctors();
    }

    /**
     * 获取所有科室列表
     */
    @GetMapping("/department/list")
    public List<Department> listDepartments() {
        return departmentMapper.selectAll();
    }

    /**
     * 医生统计（接诊量 + 复查率）
     */
    @GetMapping("/statistics/doctor")
    public List<DoctorStatsVO> getDoctorStats() {
        return statisticsService.getDoctorStats();
    }

    /**
     * 部门统计
     */
    @GetMapping("/statistics/dept")
    public List<DeptStatsVO> getDeptStats() {
        return statisticsService.getDeptStats();
    }
}