package com.neuedu.his.controller;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.AdminService;
import com.neuedu.his.service.DashboardService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

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
}
