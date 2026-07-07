package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

public interface AdminService {
    StaffCreateResponseVO createStaff(StaffCreateRequestDTO request);
    Integer createEmployee(StaffCreateRequestDTO request);
    java.util.List<EmployeeListItemVO> listEmployees(String roleType);
    java.util.List<PatientDepartmentVO> listDepartments();
    java.util.List<DoctorStatsVO> getDoctorStats();
    java.util.List<DepartmentStatsVO> getDepartmentStats();
    void charge(ChargeRequestDTO request);
    void refund(RefundRequestDTO request);
    java.util.List<ChargeItemVO> getPendingItems(Integer registerId);
    java.util.List<ChargeItemVO> getPaidItems(Integer registerId);
    PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query);
    DailySummaryVO getDailySummary(DailySummaryQueryDTO query);
    void dispense(DispenseRequestDTO request);
    void drugRefund(DrugRefundRequestDTO request);
    java.util.List<PrescriptionWorkItemVO> getPendingDispense();
    java.util.List<PrescriptionWorkItemVO> getPendingRefund();
    PageResult<DrugInventoryVO> getDrugInventory(DrugInventoryQueryDTO query);
}
