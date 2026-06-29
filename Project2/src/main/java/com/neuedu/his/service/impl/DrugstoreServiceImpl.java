package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.DrugInfoMapper;
import com.neuedu.his.mapper.DrugStockRecordMapper;
import com.neuedu.his.mapper.PrescriptionDetailMapper;
import com.neuedu.his.mapper.PrescriptionMapper;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.DrugInfo;
import com.neuedu.his.model.entity.DrugStockRecord;
import com.neuedu.his.model.entity.Prescription;
import com.neuedu.his.model.entity.PrescriptionDetail;
import com.neuedu.his.model.vo.DrugInventoryVO;
import com.neuedu.his.model.vo.DrugStockRecordVO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.service.DrugstoreService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.List;

@Service
public class DrugstoreServiceImpl implements DrugstoreService {

    @Autowired
    private DrugInfoMapper drugInfoMapper;
    @Autowired
    private DrugStockRecordMapper drugStockRecordMapper;
    @Autowired
    private PrescriptionMapper prescriptionMapper;
    @Autowired
    private PrescriptionDetailMapper prescriptionDetailMapper;

    @Override
    public PageResult<DrugInventoryVO> getInventory(DrugInventoryQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<DrugInfo> list = drugInfoMapper.selectByCondition(query.getDrugName(), query.getDrugType(), query.getStockAlert());
        return toInventoryPage(list);
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void stockIn(DrugStockInRequestDTO request) {
        DrugInfo drug = requireDrug(request.getDrugId());
        int before = safeStock(drug);
        int after = before + request.getQuantity();
        drugInfoMapper.updateStock(drug.getId(), after);
        record(drug.getId(), "IN", request.getQuantity(), before, after, request.getOperatorId(), null, request.getReason());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void stockCheck(DrugStockCheckRequestDTO request) {
        DrugInfo drug = requireDrug(request.getDrugId());
        int before = safeStock(drug);
        int after = request.getActualStock();
        drugInfoMapper.updateStock(drug.getId(), after);
        record(drug.getId(), "CHECK", Math.abs(after - before), before, after, request.getOperatorId(), null, request.getReason());
    }

    @Override
    public PageResult<DrugInventoryVO> getAlerts(Integer threshold, Integer pageNum, Integer pageSize) {
        int limit = threshold == null ? 10 : threshold;
        PageHelper.startPage(pageNum == null ? 1 : pageNum, pageSize == null ? 10 : pageSize);
        return toInventoryPage(drugInfoMapper.selectLowStock(limit));
    }

    @Override
    public PageResult<DrugStockRecordVO> getStockRecords(Integer drugId, String recordType, Integer pageNum, Integer pageSize) {
        PageHelper.startPage(pageNum == null ? 1 : pageNum, pageSize == null ? 10 : pageSize);
        List<DrugStockRecordVO> list = drugStockRecordMapper.selectByCondition(drugId, recordType);
        PageInfo<DrugStockRecordVO> pageInfo = new PageInfo<>(list);
        PageResult<DrugStockRecordVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(list);
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispense(DispenseRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"CHARGED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("处方未收费或状态异常，无法发药");
        }
        List<PrescriptionDetail> details = prescriptionDetailMapper.selectByPrescriptionId(request.getPrescriptionId());
        for (PrescriptionDetail detail : details) {
            DrugInfo drug = requireDrug(detail.getDrugId());
            int before = safeStock(drug);
            int quantity = detail.getDrugNumber() == null ? 0 : detail.getDrugNumber();
            if (before < quantity) {
                throw new BusinessException("药品库存不足：" + drug.getDrugName());
            }
            int after = before - quantity;
            drugInfoMapper.updateStock(drug.getId(), after);
            record(drug.getId(), "DISPENSE", quantity, before, after, request.getPharmacistId(), request.getPrescriptionId(), "处方发药");
        }
        prescriptionMapper.dispense(request.getPrescriptionId(), request.getPharmacistId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void refund(DrugRefundRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"DISPENSED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("处方未发药，无法退药");
        }
        List<PrescriptionDetail> details = prescriptionDetailMapper.selectByPrescriptionId(request.getPrescriptionId());
        for (PrescriptionDetail detail : details) {
            DrugInfo drug = requireDrug(detail.getDrugId());
            int before = safeStock(drug);
            int quantity = detail.getDrugNumber() == null ? 0 : detail.getDrugNumber();
            int after = before + quantity;
            drugInfoMapper.updateStock(drug.getId(), after);
            record(drug.getId(), "REFUND", quantity, before, after, request.getPharmacistId(), request.getPrescriptionId(), request.getRefundReason());
        }
        prescriptionMapper.updateStatusAndAmount(request.getPrescriptionId(), "REFUNDED", null);
    }

    private PageResult<DrugInventoryVO> toInventoryPage(List<DrugInfo> list) {
        PageInfo<DrugInfo> pageInfo = new PageInfo<>(list);
        List<DrugInventoryVO> voList = new ArrayList<>();
        for (DrugInfo drug : list) {
            DrugInventoryVO vo = new DrugInventoryVO();
            vo.setDrugId(drug.getId());
            vo.setDrugCode(drug.getDrugCode());
            vo.setDrugName(drug.getDrugName());
            vo.setDrugFormat(drug.getDrugFormat());
            vo.setDrugUnit(drug.getDrugUnit());
            vo.setStockNum(safeStock(drug));
            vo.setDrugPrice(drug.getDrugPrice());
            vo.setManufacturer(drug.getManufacturer());
            vo.setAlert(safeStock(drug) < 10);
            voList.add(vo);
        }
        PageResult<DrugInventoryVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    private DrugInfo requireDrug(Integer drugId) {
        DrugInfo drug = drugInfoMapper.selectById(drugId);
        if (drug == null) {
            throw new BusinessException("药品不存在");
        }
        return drug;
    }

    private int safeStock(DrugInfo drug) {
        return drug.getStockNum() == null ? 0 : drug.getStockNum();
    }

    private void record(Integer drugId, String type, Integer quantity, Integer before, Integer after,
                        Integer operatorId, Integer prescriptionId, String reason) {
        DrugStockRecord record = new DrugStockRecord();
        record.setDrugId(drugId);
        record.setRecordType(type);
        record.setQuantity(quantity == null ? 0 : quantity);
        record.setBeforeStock(before);
        record.setAfterStock(after);
        record.setOperatorId(operatorId);
        record.setRelatedPrescriptionId(prescriptionId);
        record.setReason(reason);
        drugStockRecordMapper.insert(record);
    }
}
