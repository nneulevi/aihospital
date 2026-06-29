package com.neuedu.his.controller;

import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.model.vo.DrugInventoryVO;
import com.neuedu.his.model.vo.DrugStockRecordVO;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.service.DrugstoreService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/drugstore")
public class DrugstoreController {

    @Autowired
    private DrugstoreService drugstoreService;

    @GetMapping("/inventory")
    public PageResult<DrugInventoryVO> getInventory(
            @Valid DrugInventoryQueryDTO query) {
        return drugstoreService.getInventory(query);
    }

    @PostMapping("/stock/in")
    public void stockIn(@RequestBody @Valid DrugStockInRequestDTO request) {
        drugstoreService.stockIn(request);
    }

    @PostMapping("/stock/check")
    public void stockCheck(@RequestBody @Valid DrugStockCheckRequestDTO request) {
        drugstoreService.stockCheck(request);
    }

    @GetMapping("/stock/alerts")
    public PageResult<DrugInventoryVO> getAlerts(@RequestParam(defaultValue = "10") Integer threshold,
                                                 @RequestParam(defaultValue = "1") Integer pageNum,
                                                 @RequestParam(defaultValue = "10") Integer pageSize) {
        return drugstoreService.getAlerts(threshold, pageNum, pageSize);
    }

    @GetMapping("/stock/records")
    public PageResult<DrugStockRecordVO> getStockRecords(@RequestParam(required = false) Integer drugId,
                                                         @RequestParam(required = false) String recordType,
                                                         @RequestParam(defaultValue = "1") Integer pageNum,
                                                         @RequestParam(defaultValue = "10") Integer pageSize) {
        return drugstoreService.getStockRecords(drugId, recordType, pageNum, pageSize);
    }

    @PostMapping("/dispense")
    public void dispense(@RequestBody @Valid DispenseRequestDTO request) {
        drugstoreService.dispense(request);
    }

    @PostMapping("/refund")
    public void refund(@RequestBody @Valid DrugRefundRequestDTO request) {
        drugstoreService.refund(request);
    }
}
