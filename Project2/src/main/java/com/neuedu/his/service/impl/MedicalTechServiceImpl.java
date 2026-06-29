package com.neuedu.his.service.impl;

import com.github.pagehelper.PageHelper;
import com.github.pagehelper.PageInfo;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.CheckRequestMapper;
import com.neuedu.his.mapper.DisposalRequestMapper;
import com.neuedu.his.mapper.InspectionRequestMapper;
import com.neuedu.his.mapper.MedicalTechWorkMapper;
import com.neuedu.his.model.dto.MedicalTechExecuteRequestDTO;
import com.neuedu.his.model.dto.MedicalTechReportRequestDTO;
import com.neuedu.his.model.dto.MedicalTechTaskQueryDTO;
import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.entity.DisposalRequest;
import com.neuedu.his.model.entity.InspectionRequest;
import com.neuedu.his.model.vo.MedicalTechInterpretationVO;
import com.neuedu.his.model.vo.MedicalTechTaskVO;
import com.neuedu.his.model.vo.PageResult;
import com.neuedu.his.service.MedicalTechService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Locale;

@Service
public class MedicalTechServiceImpl implements MedicalTechService {

    @Autowired
    private MedicalTechWorkMapper medicalTechWorkMapper;
    @Autowired
    private CheckRequestMapper checkRequestMapper;
    @Autowired
    private InspectionRequestMapper inspectionRequestMapper;
    @Autowired
    private DisposalRequestMapper disposalRequestMapper;

    @Override
    public PageResult<MedicalTechTaskVO> getTasks(MedicalTechTaskQueryDTO query) {
        PageHelper.startPage(query.getPageNum(), query.getPageSize());
        List<MedicalTechTaskVO> list = medicalTechWorkMapper.selectTasks(
                query.getRegisterId(),
                normalizeType(query.getItemType()),
                query.getState()
        );
        PageInfo<MedicalTechTaskVO> pageInfo = new PageInfo<>(list);
        PageResult<MedicalTechTaskVO> result = new PageResult<>();
        result.setTotal(pageInfo.getTotal());
        result.setPageNum(pageInfo.getPageNum());
        result.setPageSize(pageInfo.getPageSize());
        result.setTotalPages(pageInfo.getPages());
        result.setRecords(list);
        return result;
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void execute(String itemType, Integer itemId, MedicalTechExecuteRequestDTO request) {
        String type = normalizeType(itemType);
        String currentState = currentState(type, itemId);
        if (!"CHARGED".equals(currentState)) {
            throw new BusinessException("医技项目未收费或状态不允许执行");
        }
        if ("CHECK".equals(type)) {
            checkRequestMapper.updateExecute(itemId, request.getExecutorId(), request.getRemark());
        } else if ("INSPECTION".equals(type)) {
            inspectionRequestMapper.updateExecute(itemId, request.getExecutorId(), request.getRemark());
        } else {
            disposalRequestMapper.updateExecute(itemId, request.getExecutorId(), request.getRemark());
        }
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public void report(String itemType, Integer itemId, MedicalTechReportRequestDTO request) {
        String type = normalizeType(itemType);
        String currentState = currentState(type, itemId);
        if (!"EXECUTING".equals(currentState) && !"COMPLETED".equals(currentState)) {
            throw new BusinessException("医技项目未执行，不能录入报告");
        }
        if ("CHECK".equals(type)) {
            checkRequestMapper.updateResult(itemId, request.getResult(), request.getReporterId(), request.getRemark());
        } else if ("INSPECTION".equals(type)) {
            inspectionRequestMapper.updateResult(itemId, request.getResult(), request.getReporterId(), request.getRemark());
        } else {
            disposalRequestMapper.updateResult(itemId, request.getResult(), request.getReporterId(), request.getRemark());
        }
    }

    @Override
    public MedicalTechInterpretationVO aiInterpret(String itemType, Integer itemId) {
        String type = normalizeType(itemType);
        String resultText = resultText(type, itemId);
        if (resultText == null || resultText.isBlank()) {
            throw new BusinessException("医技项目尚未录入结果，不能进行 AI 解读");
        }
        MedicalTechInterpretationVO vo = new MedicalTechInterpretationVO();
        vo.setItemType(type);
        vo.setItemId(itemId);
        vo.setSummary("AI解读：" + resultText);
        vo.setSuggestion("请结合患者症状、体征及医生诊断进行复核，AI结果仅作辅助。");
        return vo;
    }

    private String normalizeType(String itemType) {
        if (itemType == null || itemType.isBlank()) {
            return null;
        }
        String value = itemType.trim().toUpperCase(Locale.ROOT);
        if (!"CHECK".equals(value) && !"INSPECTION".equals(value) && !"DISPOSAL".equals(value)) {
            throw new BusinessException("不支持的医技项目类型：" + itemType);
        }
        return value;
    }

    private String currentState(String type, Integer itemId) {
        if ("CHECK".equals(type)) {
            CheckRequest request = checkRequestMapper.selectById(itemId);
            if (request == null) throw new BusinessException("检查项目不存在");
            return request.getCheckState();
        }
        if ("INSPECTION".equals(type)) {
            InspectionRequest request = inspectionRequestMapper.selectById(itemId);
            if (request == null) throw new BusinessException("检验项目不存在");
            return request.getInspectionState();
        }
        DisposalRequest request = disposalRequestMapper.selectById(itemId);
        if (request == null) throw new BusinessException("处置项目不存在");
        return request.getDisposalState();
    }

    private String resultText(String type, Integer itemId) {
        if ("CHECK".equals(type)) {
            CheckRequest request = checkRequestMapper.selectById(itemId);
            if (request == null) throw new BusinessException("检查项目不存在");
            return request.getCheckResult();
        }
        if ("INSPECTION".equals(type)) {
            InspectionRequest request = inspectionRequestMapper.selectById(itemId);
            if (request == null) throw new BusinessException("检验项目不存在");
            return request.getInspectionResult();
        }
        DisposalRequest request = disposalRequestMapper.selectById(itemId);
        if (request == null) throw new BusinessException("处置项目不存在");
        return request.getDisposalResult();
    }
}
