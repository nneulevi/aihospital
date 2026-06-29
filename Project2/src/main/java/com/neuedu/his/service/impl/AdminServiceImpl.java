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
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

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
    private MedicalTechnologyMapper medicalTechnologyMapper;
    @Autowired
    private FinanceRecordMapper financeRecordMapper;
    @Autowired
    private DrugStockRecordMapper drugStockRecordMapper;

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void charge(ChargeRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        List<ChargeItem> items = resolveChargeItems(request.getRegisterId(), request.getItemIds(), request.getItemTypes(), "CREATED");
        BigDecimal shouldPay = sumAmount(items);
        if (shouldPay.compareTo(request.getAmount()) != 0) {
            throw new BusinessException("缴费金额不正确，应付：" + shouldPay);
        }

        for (ChargeItem item : items) {
            updateItemState(item, "CHARGED");
            financeRecordMapper.insert(toFinanceRecord(request.getRegisterId(), item, request.getChargeMethod(), "CHARGE"));
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void refund(RefundRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        List<ChargeItem> items = resolveChargeItems(request.getRegisterId(), request.getItemIds(), request.getItemTypes(), "CHARGED");
        BigDecimal shouldRefund = sumAmount(items);
        if (request.getRefundAmount() != null && shouldRefund.compareTo(request.getRefundAmount()) != 0) {
            throw new BusinessException("退费金额不正确，应退：" + shouldRefund);
        }

        for (ChargeItem item : items) {
            updateItemState(item, "REFUNDED");
            financeRecordMapper.insert(toFinanceRecord(request.getRegisterId(), item, "REFUND", "REFUND"));
        }
    }

    @Override
    public PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        LocalDateTime startTime = query.getStartDate() == null ? null : query.getStartDate().atStartOfDay();
        LocalDateTime endTimeExclusive = query.getEndDate() == null ? null : query.getEndDate().plusDays(1).atStartOfDay();
        List<FinanceRecordVO> voList = financeRecordMapper.selectByCondition(
                startTime,
                endTimeExclusive,
                query.getChargeMethod(),
                query.getRecordType()
        );
        PageInfo<FinanceRecordVO> pageInfo = new PageInfo<>(voList);

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
        LocalDateTime startTime = query.getSummaryDate().atStartOfDay();
        LocalDateTime endTimeExclusive = query.getSummaryDate().plusDays(1).atStartOfDay();
        List<FinanceRecordVO> records = financeRecordMapper.selectByCondition(startTime, endTimeExclusive, null, null);

        DailySummaryVO summary = new DailySummaryVO();
        summary.setSummaryDate(query.getSummaryDate());
        summary.setTotalTransactions(records.size());
        summary.setChargeCount(0);
        summary.setRefundCount(0);
        summary.setTotalAmount(BigDecimal.ZERO);
        summary.setRefundAmount(BigDecimal.ZERO);
        summary.setOperatorName("系统汇总");

        for (FinanceRecordVO record : records) {
            BigDecimal amount = record.getAmount() == null ? BigDecimal.ZERO : record.getAmount();
            if ("REFUND".equals(record.getRecordType())) {
                summary.setRefundCount(summary.getRefundCount() + 1);
                summary.setRefundAmount(summary.getRefundAmount().add(amount));
            } else {
                summary.setChargeCount(summary.getChargeCount() + 1);
                summary.setTotalAmount(summary.getTotalAmount().add(amount));
            }
        }
        return summary;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispense(DispenseRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"CHARGED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("该处方未缴费或状态异常，无法发药");
        }

        List<PrescriptionDetail> details = prescriptionDetailMapper.selectByPrescriptionId(request.getPrescriptionId());
        for (PrescriptionDetail detail : details) {
            DrugInfo drug = drugInfoMapper.selectById(detail.getDrugId());
            if (drug == null) {
                throw new BusinessException("药品不存在");
            }
            int before = drug.getStockNum() == null ? 0 : drug.getStockNum();
            int quantity = detail.getDrugNumber() == null ? 0 : detail.getDrugNumber();
            if (before < quantity) {
                throw new BusinessException("药品库存不足：" + drug.getDrugName());
            }
            int after = before - quantity;
            drugInfoMapper.updateStock(drug.getId(), after);
            insertStockRecord(drug.getId(), "DISPENSE", quantity, before, after, request.getPharmacistId(), request.getPrescriptionId(), "管理员发药");
        }
        prescriptionMapper.dispense(request.getPrescriptionId(), request.getPharmacistId());
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void drugRefund(DrugRefundRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"DISPENSED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("该处方未发药，无法退药");
        }

        List<PrescriptionDetail> details = prescriptionDetailMapper.selectByPrescriptionId(request.getPrescriptionId());
        for (PrescriptionDetail detail : details) {
            DrugInfo drug = drugInfoMapper.selectById(detail.getDrugId());
            if (drug != null) {
                int before = drug.getStockNum() == null ? 0 : drug.getStockNum();
                int quantity = detail.getDrugNumber() == null ? 0 : detail.getDrugNumber();
                int after = before + quantity;
                drugInfoMapper.updateStock(drug.getId(), after);
                insertStockRecord(drug.getId(), "REFUND", quantity, before, after, request.getPharmacistId(), request.getPrescriptionId(), request.getRefundReason());
            }
        }

        prescriptionMapper.updateStatusAndAmount(request.getPrescriptionId(), "REFUNDED", null);
        ChargeItem refundItem = new ChargeItem(
                prescription.getId(),
                "PRESCRIPTION",
                "处方",
                prescription.getTotalAmount()
        );
        financeRecordMapper.insert(toFinanceRecord(prescription.getRegisterId(), refundItem, "REFUND", "REFUND"));
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
            vo.setDrugName(d.getDrugName());
            vo.setStockNum(d.getStockNum());
            vo.setAlert(d.getStockNum() < 10);
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

    private BigDecimal sumAmount(List<ChargeItem> items) {
        BigDecimal total = BigDecimal.ZERO;
        for (ChargeItem item : items) {
            total = total.add(item.amount);
        }
        return total;
    }

    private List<ChargeItem> resolveChargeItems(Integer registerId, List<Integer> itemIds, List<String> itemTypes, String expectedState) {
        if (itemIds == null || itemIds.isEmpty()) {
            throw new BusinessException("收费项目不能为空");
        }

        List<ChargeItem> items = new ArrayList<>();
        for (int i = 0; i < itemIds.size(); i++) {
            Integer itemId = itemIds.get(i);
            String itemType = itemTypes != null && i < itemTypes.size() ? itemTypes.get(i) : null;
            ChargeItem item = resolveChargeItem(registerId, itemId, itemType, expectedState);
            items.add(item);
        }
        return items;
    }

    private ChargeItem resolveChargeItem(Integer registerId, Integer itemId, String itemType, String expectedState) {
        if (itemType != null && !itemType.isBlank()) {
            return resolveTypedChargeItem(registerId, itemId, itemType, expectedState);
        }

        ChargeItem item = tryResolveTypedChargeItem(registerId, itemId, "PRESCRIPTION", expectedState);
        if (item != null) return item;
        item = tryResolveTypedChargeItem(registerId, itemId, "CHECK", expectedState);
        if (item != null) return item;
        item = tryResolveTypedChargeItem(registerId, itemId, "INSPECTION", expectedState);
        if (item != null) return item;
        item = tryResolveTypedChargeItem(registerId, itemId, "DISPOSAL", expectedState);
        if (item != null) return item;
        throw new BusinessException("收费项目不存在或状态不允许操作：" + itemId);
    }

    private ChargeItem resolveTypedChargeItem(Integer registerId, Integer itemId, String itemType, String expectedState) {
        ChargeItem item = tryResolveTypedChargeItem(registerId, itemId, itemType, expectedState);
        if (item == null) {
            throw new BusinessException("收费项目不存在或状态不允许操作：" + itemType + "#" + itemId);
        }
        return item;
    }

    private ChargeItem tryResolveTypedChargeItem(Integer registerId, Integer itemId, String itemType, String expectedState) {
        String normalizedType = normalizeItemType(itemType);
        if ("PRESCRIPTION".equals(normalizedType)) {
            Prescription prescription = prescriptionMapper.selectById(itemId);
            if (prescription == null
                    || !registerId.equals(prescription.getRegisterId())
                    || !expectedState.equals(prescription.getPrescriptionStatus())) {
                return null;
            }
            return new ChargeItem(itemId, normalizedType, "处方", prescription.getTotalAmount());
        }

        if ("CHECK".equals(normalizedType)) {
            CheckRequest check = checkRequestMapper.selectById(itemId);
            if (check == null
                    || !registerId.equals(check.getRegisterId())
                    || !expectedState.equals(check.getCheckState())) {
                return null;
            }
            MedicalTechnology tech = medicalTechnologyMapper.selectById(check.getMedicalTechnologyId());
            return new ChargeItem(itemId, normalizedType, tech != null ? tech.getTechName() : "检查项目",
                    tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
        }

        if ("INSPECTION".equals(normalizedType)) {
            InspectionRequest inspection = inspectionRequestMapper.selectById(itemId);
            if (inspection == null
                    || !registerId.equals(inspection.getRegisterId())
                    || !expectedState.equals(inspection.getInspectionState())) {
                return null;
            }
            MedicalTechnology tech = medicalTechnologyMapper.selectById(inspection.getMedicalTechnologyId());
            return new ChargeItem(itemId, normalizedType, tech != null ? tech.getTechName() : "检验项目",
                    tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
        }

        if ("DISPOSAL".equals(normalizedType)) {
            DisposalRequest disposal = disposalRequestMapper.selectById(itemId);
            if (disposal == null
                    || !registerId.equals(disposal.getRegisterId())
                    || !expectedState.equals(disposal.getDisposalState())) {
                return null;
            }
            MedicalTechnology tech = medicalTechnologyMapper.selectById(disposal.getMedicalTechnologyId());
            return new ChargeItem(itemId, normalizedType, tech != null ? tech.getTechName() : "处置项目",
                    tech != null ? tech.getTechPrice() : BigDecimal.ZERO);
        }

        throw new BusinessException("不支持的收费项目类型：" + itemType);
    }

    private void updateItemState(ChargeItem item, String state) {
        if ("PRESCRIPTION".equals(item.type)) {
            prescriptionMapper.updateStatusAndAmount(item.id, state, null);
            return;
        }
        if ("CHECK".equals(item.type)) {
            checkRequestMapper.updateState(item.id, state);
            return;
        }
        if ("INSPECTION".equals(item.type)) {
            inspectionRequestMapper.updateState(item.id, state);
            return;
        }
        if ("DISPOSAL".equals(item.type)) {
            disposalRequestMapper.updateState(item.id, state);
        }
    }

    private String normalizeItemType(String itemType) {
        if (itemType == null || itemType.isBlank()) {
            return null;
        }
        String value = itemType.trim().toUpperCase(Locale.ROOT);
        if ("DRUG".equals(value)) {
            return "PRESCRIPTION";
        }
        return value;
    }

    private FinanceRecord toFinanceRecord(Integer registerId, ChargeItem item, String chargeMethod, String recordType) {
        FinanceRecord record = new FinanceRecord();
        record.setRecordNo(recordType + "-" + registerId + "-" + item.type + "-" + item.id + "-" + System.currentTimeMillis());
        record.setRegisterId(registerId);
        record.setItemId(item.id);
        record.setItemType(item.type);
        record.setItemName(item.name);
        record.setAmount(item.amount);
        record.setChargeMethod(chargeMethod);
        record.setRecordType(recordType);
        record.setOperatorName("系统收费员");
        return record;
    }

    private void insertStockRecord(Integer drugId, String type, Integer quantity, Integer before, Integer after,
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

    private static class ChargeItem {
        private final Integer id;
        private final String type;
        private final String name;
        private final BigDecimal amount;

        private ChargeItem(Integer id, String type, String name, BigDecimal amount) {
            this.id = id;
            this.type = type;
            this.name = name;
            this.amount = amount != null ? amount : BigDecimal.ZERO;
        }
    }
}
