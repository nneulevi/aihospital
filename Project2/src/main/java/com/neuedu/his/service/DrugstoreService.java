package com.neuedu.his.service;

import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.vo.DrugInventoryVO;
import com.neuedu.his.model.vo.DrugStockRecordVO;
import com.neuedu.his.model.vo.PageResult;

public interface DrugstoreService {
    PageResult<DrugInventoryVO> getInventory(DrugInventoryQueryDTO query);
    void stockIn(DrugStockInRequestDTO request);
    void stockCheck(DrugStockCheckRequestDTO request);
    PageResult<DrugInventoryVO> getAlerts(Integer threshold, Integer pageNum, Integer pageSize);
    PageResult<DrugStockRecordVO> getStockRecords(Integer drugId, String recordType, Integer pageNum, Integer pageSize);
    void dispense(DispenseRequestDTO request);
    void refund(DrugRefundRequestDTO request);
}
