package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.*;

public interface AdminService {
    void charge(ChargeRequestDTO request);
    void refund(RefundRequestDTO request);
    PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query);
    DailySummaryVO getDailySummary(DailySummaryQueryDTO query);
    void dispense(DispenseRequestDTO request);
    void drugRefund(DrugRefundRequestDTO request);
    PageResult<DrugInventoryVO> getDrugInventory(DrugInventoryQueryDTO query);
}