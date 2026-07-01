package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.ChargeItem;
import com.neuedu.his.model.vo.*;

import java.util.List;

public interface AdminService {
    void charge(ChargeRequestDTO request, Integer operatorId);
    void refund(RefundRequestDTO request, Integer operatorId);
    PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query);
    DailySummaryVO getDailySummary(DailySummaryQueryDTO query);
    void dispense(DispenseRequestDTO request);
    void drugRefund(DrugRefundRequestDTO request);
    PageResult<DrugInventoryVO> getDrugInventory(DrugInventoryQueryDTO query);
    List<ChargeItem> getPendingItems(Integer registerId);
    List<ChargeItem> getPaidItems(Integer registerId);
    List<PrescriptionDispenseVO> getPendingDispense();
    List<PrescriptionRefundVO> getPendingRefund();
}
