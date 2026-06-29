package com.neuedu.his.service.impl;

import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.mapper.AiImageAnalysisMapper;
import com.neuedu.his.mapper.AiImageFileMapper;
import com.neuedu.his.mapper.CheckRequestMapper;
import com.neuedu.his.mapper.RegisterMapper;
import com.neuedu.his.model.dto.ImageAnalyzeRequestDTO;
import com.neuedu.his.model.dto.ImageUploadRequestDTO;
import com.neuedu.his.model.entity.AiImageAnalysis;
import com.neuedu.his.model.entity.AiImageFile;
import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.entity.Register;
import com.neuedu.his.model.vo.ImageAnalyzeResponseVO;
import com.neuedu.his.service.HeadCtAiWorkflowService;
import com.neuedu.his.service.ImageService;
import com.neuedu.his.util.FileUploadUtil;
import com.neuedu.his.util.JsonUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.util.StringUtils;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public class ImageServiceRealImpl implements ImageService {

    @Autowired
    private AiImageAnalysisMapper aiImageAnalysisMapper;

    @Autowired
    private AiImageFileMapper aiImageFileMapper;

    @Autowired
    private CheckRequestMapper checkRequestMapper;

    @Autowired
    private RegisterMapper registerMapper;

    @Autowired
    private HeadCtAiWorkflowService headCtAiWorkflowService;

    @Override
    public String upload(ImageUploadRequestDTO request, MultipartFile file) {
        CheckRequest checkRequest = checkRequestMapper.selectById(request.getCheckRequestId());
        if (checkRequest == null) {
            throw new BusinessException("检查申请不存在: " + request.getCheckRequestId());
        }

        String filePath = FileUploadUtil.save(file, "ct/" + request.getRegisterId());

        AiImageFile imageFile = new AiImageFile();
        imageFile.setCheckRequestId(request.getCheckRequestId());
        imageFile.setRegisterId(request.getRegisterId());
        imageFile.setFilePath(filePath);
        imageFile.setFileName(file.getOriginalFilename());
        imageFile.setFileSize(file.getSize());
        imageFile.setFileFormat(resolveFileFormat(file));
        imageFile.setUploadBy(0);
        aiImageFileMapper.insert(imageFile);

        Map<String, Object> response = new LinkedHashMap<>();
        response.put("imageFileId", imageFile.getId());
        response.put("filePath", filePath);
        response.put("fileName", file.getOriginalFilename());
        return JsonUtil.toJson(response);
    }

    @Override
    public ImageAnalyzeResponseVO analyze(ImageAnalyzeRequestDTO request) {
        AiImageFile imageFile = aiImageFileMapper.selectById(request.getImageFileId());
        if (imageFile == null) {
            throw new BusinessException("影像文件不存在: " + request.getImageFileId());
        }

        CheckRequest checkRequest = checkRequestMapper.selectById(request.getCheckRequestId());
        if (checkRequest == null) {
            throw new BusinessException("检查申请不存在: " + request.getCheckRequestId());
        }

        Register register = registerMapper.selectById(checkRequest.getRegisterId());
        Map<String, Object> result = headCtAiWorkflowService.createAndWaitAnalysis(imageFile, checkRequest, register);

        String findings = extractFindings(result);
        String conclusion = extractConclusion(result);
        double confidence = extractConfidence(result);

        AiImageAnalysis analysis = new AiImageAnalysis();
        analysis.setCheckRequestId(checkRequest.getId());
        analysis.setRegisterId(checkRequest.getRegisterId());
        analysis.setFilePath(imageFile.getFilePath());
        analysis.setAiFindings(findings);
        analysis.setAiAnnotation(JsonUtil.toJson(result));
        analysis.setAiConclusion(conclusion);
        analysis.setConfidence(BigDecimal.valueOf(confidence));
        analysis.setAiModelVersion(firstText(result.get("module_version"), result.get("pipeline_version"), "HeadCTOrchestrator"));
        aiImageAnalysisMapper.insert(analysis);

        ImageAnalyzeResponseVO response = new ImageAnalyzeResponseVO();
        response.setAnalysisId(analysis.getId());
        response.setFindings(findings);
        response.setConclusion(conclusion);
        response.setConfidence(confidence);
        response.setAnnotations(extractAnnotations(result));
        response.setAiImagingStatus(asMap(result.get("ai_imaging_status")));
        return response;
    }

    private String resolveFileFormat(MultipartFile file) {
        if (StringUtils.hasText(file.getContentType())) {
            return file.getContentType();
        }
        String name = file.getOriginalFilename();
        if (name == null || !name.contains(".")) {
            return "unknown";
        }
        return name.substring(name.lastIndexOf('.') + 1).toLowerCase();
    }

    private String extractFindings(Map<String, Object> result) {
        Map<String, Object> reportAssist = asMap(result.get("report_assist"));
        Map<String, Object> lesionAnalysis = asMap(result.get("lesion_analysis"));
        Map<String, Object> lesionSummary = asMap(lesionAnalysis.get("summary"));
        Map<String, Object> qualityControl = asMap(result.get("quality_control"));

        return firstText(
                reportAssist.get("findings"),
                reportAssist.get("summary"),
                reportAssist.get("report_suggestion"),
                lesionSummary.get("finding"),
                lesionSummary.get("text"),
                qualityControl.get("report_suggestion"),
                "头部CT AI分析已完成，详见结构化结果快照"
        );
    }

    private String extractConclusion(Map<String, Object> result) {
        Map<String, Object> reportAssist = asMap(result.get("report_assist"));
        return firstText(
                reportAssist.get("impression"),
                reportAssist.get("conclusion"),
                reportAssist.get("lesion_text"),
                result.get("analysis_reliability"),
                "请结合临床病史及医生审核意见综合判断"
        );
    }

    private double extractConfidence(Map<String, Object> result) {
        Map<String, Object> lesionAnalysis = asMap(result.get("lesion_analysis"));
        Map<String, Object> lesionSummary = asMap(lesionAnalysis.get("summary"));
        Object value = firstObject(
                lesionSummary.get("highest_confidence"),
                lesionSummary.get("confidence"),
                result.get("confidence")
        );
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value != null) {
            try {
                return Double.parseDouble(value.toString());
            } catch (NumberFormatException ignored) {
                return 0.0;
            }
        }
        return 0.0;
    }

    private List<ImageAnalyzeResponseVO.Annotation> extractAnnotations(Map<String, Object> result) {
        List<ImageAnalyzeResponseVO.Annotation> annotations = new ArrayList<>();
        Map<String, Object> lesionAnalysis = asMap(result.get("lesion_analysis"));
        Object affectedSlices = lesionAnalysis.get("affected_slices");
        if (affectedSlices instanceof List<?> slices) {
            for (Object slice : slices) {
                ImageAnalyzeResponseVO.Annotation annotation = new ImageAnalyzeResponseVO.Annotation();
                annotation.setX(0);
                annotation.setY(0);
                annotation.setWidth(0);
                annotation.setHeight(0);
                annotation.setLabel("affected_slice:" + Objects.toString(slice, ""));
                annotations.add(annotation);
            }
        }
        return annotations;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> asMap(Object value) {
        if (value instanceof Map<?, ?> map) {
            return (Map<String, Object>) map;
        }
        return new LinkedHashMap<>();
    }

    private Object firstObject(Object... values) {
        for (Object value : values) {
            if (value != null) {
                return value;
            }
        }
        return null;
    }

    private String firstText(Object... values) {
        for (Object value : values) {
            String text = Objects.toString(value, null);
            if (StringUtils.hasText(text)) {
                return text;
            }
        }
        return "";
    }
}
