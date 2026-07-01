package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.*;
import com.neuedu.his.model.dto.*;
import com.neuedu.his.model.entity.*;
import com.neuedu.his.model.vo.*;
import com.neuedu.his.service.AdminService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class AdminServiceImpl implements AdminService {

    @Autowired
    private RegisterMapper registerMapper;
    @Autowired
    private PrescriptionMapper prescriptionMapper;
    @Autowired
    private PrescriptionDetailMapper prescriptionDetailMapper;
    @Autowired
    private DrugInfoMapper drugInfoMapper;
    @Autowired
    private CheckRequestMapper checkRequestMapper;
    @Autowired
    private InspectionRequestMapper inspectionRequestMapper;
    @Autowired
    private DisposalRequestMapper disposalRequestMapper;
    @Autowired
    private ChargeItemMapper chargeItemMapper;
    @Autowired
    private FinanceRecordMapper financeRecordMapper;
    @Autowired
    private DrugRefundMapper drugRefundMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void charge(ChargeRequestDTO request, Integer operatorId) {
        if (request.getItemIds() == null || request.getItemIds().isEmpty()) {
            throw new BusinessException("Item ids cannot be empty");
        }

        List<Long> ids = request.getItemIds().stream().map(Integer::longValue).collect(Collectors.toList());
        List<ChargeItem> pendingItems = chargeItemMapper.selectPendingByIds(ids);
        if (pendingItems.size() != ids.size()) {
            throw new BusinessException("Some items are not in pending status or do not exist");
        }

        BigDecimal shouldPay = BigDecimal.ZERO;
        for (ChargeItem item : pendingItems) {
            shouldPay = shouldPay.add(item.getAmount());
        }
        if (shouldPay.compareTo(request.getAmount()) != 0) {
            throw new BusinessException("Incorrect charge amount, should pay: " + shouldPay);
        }

        Long registerId = pendingItems.get(0).getRegisterId();

        FinanceRecord financeRecord = new FinanceRecord();
        financeRecord.setRecordNo(generateRecordNo());
        financeRecord.setRegisterId(registerId);
        financeRecord.setRecordType("CHARGE");
        financeRecord.setTotalAmount(shouldPay);
        financeRecord.setItemCount(pendingItems.size());
        financeRecord.setChargeMethod(request.getChargeMethod());
        financeRecord.setOperatorId(operatorId);
        financeRecordMapper.insert(financeRecord);

        for (ChargeItem item : pendingItems) {
            chargeItemMapper.charge(item.getId(), financeRecord.getId(), request.getChargeMethod(), operatorId);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void refund(RefundRequestDTO request, Integer operatorId) {
        if (request.getItemIds() == null || request.getItemIds().isEmpty()) {
            throw new BusinessException("Item ids cannot be empty");
        }

        List<Long> ids = request.getItemIds().stream().map(Integer::longValue).collect(Collectors.toList());
        List<ChargeItem> chargedItems = chargeItemMapper.selectChargedByIds(ids);
        if (chargedItems.size() != ids.size()) {
            throw new BusinessException("Some items are not in charged status or do not exist");
        }

        BigDecimal shouldRefund = BigDecimal.ZERO;
        for (ChargeItem item : chargedItems) {
            shouldRefund = shouldRefund.add(item.getAmount());
        }
        if (shouldRefund.compareTo(request.getRefundAmount()) != 0) {
            throw new BusinessException("Incorrect refund amount, should refund: " + shouldRefund);
        }

        for (ChargeItem item : chargedItems) {
            if ("PRESCRIPTION".equals(item.getSourceType()) && item.getSourceId() != null) {
                Prescription prescription = prescriptionMapper.selectById(item.getSourceId().intValue());
                if (prescription != null && "DISPENSED".equals(prescription.getPrescriptionStatus())) {
                    throw new BusinessException("Prescription has been dispensed, please refund drug first");
                }
            }
        }

        Long registerId = chargedItems.get(0).getRegisterId();

        FinanceRecord financeRecord = new FinanceRecord();
        financeRecord.setRecordNo(generateRecordNo());
        financeRecord.setRegisterId(registerId);
        financeRecord.setRecordType("REFUND");
        financeRecord.setTotalAmount(shouldRefund);
        financeRecord.setItemCount(chargedItems.size());
        financeRecord.setChargeMethod(null);
        financeRecord.setOperatorId(operatorId);
        financeRecordMapper.insert(financeRecord);

        for (ChargeItem item : chargedItems) {
            chargeItemMapper.refund(item.getId(), request.getRefundReason());
        }
    }

    @Override
    public PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        String status = null;
        if ("CHARGE".equals(query.getRecordType())) {
            status = "CHARGED";
        } else if ("REFUND".equals(query.getRecordType())) {
            status = "REFUNDED";
        }
        List<ChargeItemVO> list = chargeItemMapper.selectRecords(
                query.getStartDate(), query.getEndDate(), query.getChargeMethod(), status);
        PageInfo<ChargeItemVO> pageInfo = new PageInfo<>(list);

        List<FinanceRecordVO> voList = new ArrayList<>();
        for (ChargeItemVO item : list) {
            FinanceRecordVO vo = new FinanceRecordVO();
            vo.setId(item.getId() != null ? item.getId().intValue() : null);
            vo.setRegisterId(item.getRegisterId() != null ? item.getRegisterId().intValue() : null);
            vo.setPatientName(item.getPatientName());
            vo.setItemType(item.getItemType());
            vo.setItemName(item.getItemName());
            vo.setAmount(item.getAmount());
            vo.setChargeMethod(item.getChargeMethod());
            vo.setRecordType("CHARGED".equals(item.getStatus()) ? "CHARGE" : "REFUND");
            vo.setCreateTime(item.getChargeTime() != null ? item.getChargeTime() : item.getRefundTime());
            vo.setOperatorName(item.getOperatorName());
            vo.setRecordNo(item.getFinanceRecordNo());
            voList.add(vo);
        }

        PageResult<FinanceRecordVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(voList);
        return result;
    }

    @Override
    public DailySummaryVO getDailySummary(DailySummaryQueryDTO query) {
        Map<String, Object> map = chargeItemMapper.selectDailySummary(query.getSummaryDate());
        DailySummaryVO vo = new DailySummaryVO();
        vo.setSummaryDate(query.getSummaryDate());
        if (map != null) {
            vo.setTotalTransactions(map.get("total_count") != null ? ((Number) map.get("total_count")).intValue() : 0);
            vo.setTotalAmount(map.get("charge_amount") != null ? (BigDecimal) map.get("charge_amount") : BigDecimal.ZERO);
            vo.setRefundAmount(map.get("refund_amount") != null ? (BigDecimal) map.get("refund_amount") : BigDecimal.ZERO);
            vo.setChargeCount(map.get("charge_count") != null ? ((Number) map.get("charge_count")).intValue() : 0);
            vo.setRefundCount(map.get("refund_count") != null ? ((Number) map.get("refund_count")).intValue() : 0);
        }
        vo.setOperatorName("Admin");
        return vo;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispense(DispenseRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"CHARGED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("The prescription has not been charged or status is abnormal, cannot dispense");
        }

        prescriptionMapper.dispense(request.getPrescriptionId(), request.getPharmacistId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void drugRefund(DrugRefundRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"DISPENSED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("The prescription has not been dispensed, cannot refund drug");
        }

        List<PrescriptionDetail> details = prescriptionDetailMapper.selectByPrescriptionId(request.getPrescriptionId());
        for (PrescriptionDetail detail : details) {
            DrugInfo drug = drugInfoMapper.selectById(detail.getDrugId());
            if (drug != null) {
                drugInfoMapper.updateStock(drug.getId(), drug.getStockNum() + detail.getDrugNumber());
            }
        }

        prescriptionMapper.updateStatusAndAmount(request.getPrescriptionId(), "REFUNDED", null);

        DrugRefund drugRefund = new DrugRefund();
        drugRefund.setPrescriptionId(Long.valueOf(request.getPrescriptionId()));
        drugRefund.setPharmacistId(request.getPharmacistId());
        drugRefund.setRefundReason(request.getRefundReason());
        drugRefund.setRefundAmount(prescription.getTotalAmount());
        drugRefundMapper.insert(drugRefund);

        ChargeItem chargeItem = chargeItemMapper.selectBySource(request.getPrescriptionId(), "PRESCRIPTION");
        if (chargeItem != null) {
            chargeItemMapper.refund(chargeItem.getId(), request.getRefundReason());
        }
    }

    @Override
    public PageResult<DrugInventoryVO> getDrugInventory(DrugInventoryQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<DrugInfo> list = drugInfoMapper.selectByCondition(query.getDrugName(), query.getDrugType(), query.getStockAlert());
        PageInfo<DrugInfo> pageInfo = new PageInfo<>(list);

        List<DrugInventoryVO> voList = new ArrayList<>();
        for (DrugInfo d : list) {
            DrugInventoryVO vo = new DrugInventoryVO();
            vo.setDrugId(d.getId());
            vo.setDrugCode(d.getDrugCode());
            vo.setDrugName(d.getDrugName());
            vo.setDrugFormat(d.getDrugFormat());
            vo.setDrugUnit(d.getDrugUnit());
            vo.setDrugPrice(d.getDrugPrice());
            vo.setManufacturer(d.getManufacturer());
            vo.setStockNum(d.getStockNum());
            vo.setAlert(d.getStockNum() != null && d.getStockNum() < 10);
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

    @Override
    public List<ChargeItem> getPendingItems(Integer registerId) {
        return chargeItemMapper.selectPendingByRegisterId(registerId);
    }

    @Override
    public List<ChargeItem> getPaidItems(Integer registerId) {
        return chargeItemMapper.selectChargedByRegisterId(registerId);
    }

    @Override
    public List<PrescriptionDispenseVO> getPendingDispense() {
        List<PrescriptionDispenseVO> list = prescriptionMapper.selectDispenseListByStatus("CHARGED");
        for (PrescriptionDispenseVO vo : list) {
            List<PrescriptionListVO.PrescriptionDrugSummaryVO> drugs =
                    prescriptionDetailMapper.selectDrugSummaryByPrescriptionId(vo.getPrescriptionId());
            vo.setDrugList(drugs.stream().map(PrescriptionListVO.PrescriptionDrugSummaryVO::getDrugName).collect(Collectors.toList()));
        }
        return list;
    }

    @Override
    public List<PrescriptionRefundVO> getPendingRefund() {
        List<PrescriptionDispenseVO> temp = prescriptionMapper.selectDispenseListByStatus("DISPENSED");
        List<PrescriptionRefundVO> result = new ArrayList<>();
        for (PrescriptionDispenseVO t : temp) {
            PrescriptionRefundVO vo = new PrescriptionRefundVO();
            vo.setPrescriptionId(t.getPrescriptionId());
            vo.setPrescriptionNo(t.getPrescriptionNo());
            vo.setPatientName(t.getPatientName());
            vo.setTotalAmount(t.getTotalAmount());
            vo.setStatus(t.getStatus());
            List<PrescriptionListVO.PrescriptionDrugSummaryVO> drugs =
                    prescriptionDetailMapper.selectDrugSummaryByPrescriptionId(t.getPrescriptionId());
            vo.setDrugList(drugs.stream().map(PrescriptionListVO.PrescriptionDrugSummaryVO::getDrugName).collect(Collectors.toList()));
            result.add(vo);
        }
        return result;
    }

    private String generateRecordNo() {
        String date = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        String timestamp = String.valueOf(System.currentTimeMillis());
        String suffix = timestamp.substring(Math.max(0, timestamp.length() - 6));
        return "FIN" + date + suffix;
    }
}
