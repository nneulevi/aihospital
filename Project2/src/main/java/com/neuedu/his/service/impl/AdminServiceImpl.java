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
import java.util.ArrayList;
import java.util.List;

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

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void charge(ChargeRequestDTO request) {
        Register register = registerMapper.selectById(request.getRegisterId());
        if (register == null) {
            throw new BusinessException("挂号记录不存在");
        }

        BigDecimal shouldPay = calculateAmount(request.getItemIds());
        if (shouldPay.compareTo(request.getAmount()) != 0) {
            throw new BusinessException("缴费金额不正确，应付：" + shouldPay);
        }

        for (Integer itemId : request.getItemIds()) {
            prescriptionMapper.updateStatusAndAmount(itemId, "CHARGED", null);
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void refund(RefundRequestDTO request) {
        for (Integer itemId : request.getItemIds()) {
            Prescription prescription = prescriptionMapper.selectById(itemId);
            if (prescription == null || !"CHARGED".equals(prescription.getPrescriptionStatus())) {
                throw new BusinessException("该项目未缴费或已退费，无法退费");
            }
            if ("DISPENSED".equals(prescription.getPrescriptionStatus())) {
                throw new BusinessException("该处方已发药，请先退药");
            }
        }

        for (Integer itemId : request.getItemIds()) {
            prescriptionMapper.updateStatusAndAmount(itemId, "REFUNDED", null);
        }
    }

    @Override
    public PageResult<FinanceRecordVO> getFinanceRecords(FinanceRecordsQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<FinanceRecordVO> voList = new ArrayList<>();
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
        return new DailySummaryVO();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void dispense(DispenseRequestDTO request) {
        Prescription prescription = prescriptionMapper.selectById(request.getPrescriptionId());
        if (prescription == null || !"CHARGED".equals(prescription.getPrescriptionStatus())) {
            throw new BusinessException("该处方未缴费或状态异常，无法发药");
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
                drugInfoMapper.updateStock(drug.getId(), drug.getStockNum() + detail.getDrugNumber());
            }
        }

        prescriptionMapper.updateStatusAndAmount(request.getPrescriptionId(), "REFUNDED", null);
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

    private BigDecimal calculateAmount(List<Integer> itemIds) {
        BigDecimal total = BigDecimal.ZERO;
        for (Integer itemId : itemIds) {
            Prescription prescription = prescriptionMapper.selectById(itemId);
            if (prescription != null) {
                total = total.add(prescription.getTotalAmount());
            }
        }
        return total;
    }
}