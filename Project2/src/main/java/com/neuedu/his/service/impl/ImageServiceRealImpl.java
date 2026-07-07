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
import java.util.LinkedHashSet;
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
        response.setPositiveProbability(confidence);
        response.setSubtypeProbabilities(extractSubtypeProbabilities(result));
        response.setAnalysisReliability(extractAnalysisReliability(result));
        response.setModelLimitations(extractModelLimitations(result));
        response.setAnnotations(extractAnnotations(result));
        response.setAiImagingStatus(extractAiImagingStatus(result));
        response.setPreviewUrls(extractPreviewUrls(result));
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
        Map<String, Object> firstLesion = firstLesionResult(result);
        Object affectedSlices = firstLesion.get("affected_slices");
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
        Object bbox = firstLesion.get("bbox");
        if (bbox instanceof List<?> box && box.size() >= 6) {
            ImageAnalyzeResponseVO.Annotation annotation = new ImageAnalyzeResponseVO.Annotation();
            annotation.setX(toInteger(box.get(0), 0));
            annotation.setY(toInteger(box.get(1), 0));
            annotation.setWidth(Math.max(0, toInteger(box.get(3), 0) - annotation.getX()));
            annotation.setHeight(Math.max(0, toInteger(box.get(4), 0) - annotation.getY()));
            annotation.setLabel("lesion_bbox_zyx:" + box);
            annotations.add(annotation);
        }
        return annotations;
    }

    private Map<String, Object> firstLesionResult(Map<String, Object> result) {
        Map<String, Object> lesionAnalysis = asMap(result.get("lesion_analysis"));
        Object results = lesionAnalysis.get("results");
        if (results instanceof List<?> list && !list.isEmpty()) {
            Object first = list.get(0);
            if (first instanceof Map<?, ?> map) {
                @SuppressWarnings("unchecked")
                Map<String, Object> typed = (Map<String, Object>) map;
                return typed;
            }
        }
        return new LinkedHashMap<>();
    }

    private Map<String, Double> extractSubtypeProbabilities(Map<String, Object> result) {
        Map<String, Object> firstLesion = firstLesionResult(result);
        Map<String, Object> raw = asMap(firstLesion.get("subtype_probabilities"));
        Map<String, Double> normalized = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : raw.entrySet()) {
            Double score = toDouble(entry.getValue());
            if (score != null) {
                normalized.put(entry.getKey(), Math.max(0.0, Math.min(1.0, score)));
            }
        }
        return normalized;
    }

    private String extractAnalysisReliability(Map<String, Object> result) {
        Map<String, Object> firstLesion = firstLesionResult(result);
        if (StringUtils.hasText(firstText(firstLesion.get("mask_url")))) {
            return "已输出病灶分割 mask 与叠加预览，建议结合原始影像复核";
        }
        String lesionReliability = firstText(firstLesion.get("reliability"));
        Map<String, Object> qualityControl = asMap(result.get("quality_control"));
        String severity = firstText(qualityControl.get("severity"), "unknown");
        if ("strongly_limited_by_artifact".equals(lesionReliability) || "severe".equals(severity)) {
            return "受重度伪影影响，模型结果仅作弱参考";
        }
        if ("limited_by_artifact".equals(lesionReliability) || "moderate".equals(severity)) {
            return "受伪影影响，需重点结合原始影像复核";
        }
        if ("slightly_limited_by_artifact".equals(lesionReliability) || "mild".equals(severity)) {
            return "轻度受限，建议结合相邻层面复核";
        }
        return "链路完整，当前结果按分类模型输出解释";
    }

    private List<String> extractModelLimitations(Map<String, Object> result) {
        List<String> limitations = new ArrayList<>();
        Map<String, Object> aiStatus = asMap(result.get("ai_imaging_status"));
        Object statusLimitations = aiStatus.get("limitations");
        if (statusLimitations instanceof List<?> list) {
            for (Object item : list) {
                String text = Objects.toString(item, "");
                if (StringUtils.hasText(text)) {
                    limitations.add(text);
                }
            }
        }
        Map<String, Object> firstLesion = firstLesionResult(result);
        Object warnings = firstLesion.get("warnings");
        if (warnings instanceof List<?> list) {
            for (Object item : list) {
                String text = Objects.toString(item, "");
                if (StringUtils.hasText(text)) {
                    limitations.add(text);
                }
            }
        }
        Map<String, Object> lesionModel = asMap(aiStatus.get("lesion_model"));
        if ("classification".equals(Objects.toString(lesionModel.get("task_type"), ""))) {
            limitations.add("病灶模型当前为分类模型，不输出三维病灶边界。");
        }
        return new ArrayList<>(new LinkedHashSet<>(limitations));
    }

    private Map<String, String> extractPreviewUrls(Map<String, Object> result) {
        Map<String, Object> qualityControl = asMap(result.get("quality_control"));
        Map<String, Object> previewUrls = asMap(qualityControl.get("preview_urls"));
        Map<String, Object> lesionPreviewUrls = asMap(firstLesionResult(result).get("preview_urls"));
        Map<String, String> normalized = new LinkedHashMap<>();
        for (Map.Entry<String, Object> entry : previewUrls.entrySet()) {
            String value = Objects.toString(entry.getValue(), null);
            if (StringUtils.hasText(value)) {
                normalized.put("quality_" + entry.getKey(), value);
            }
        }
        for (Map.Entry<String, Object> entry : lesionPreviewUrls.entrySet()) {
            String value = Objects.toString(entry.getValue(), null);
            if (StringUtils.hasText(value)) {
                normalized.put("lesion_" + entry.getKey(), value);
            }
        }
        return normalized;
    }

    private Map<String, Object> extractAiImagingStatus(Map<String, Object> result) {
        Map<String, Object> aiStatus = new LinkedHashMap<>(asMap(result.get("ai_imaging_status")));
        Map<String, Object> lesionModel = new LinkedHashMap<>(asMap(aiStatus.get("lesion_model")));
        Map<String, Object> firstLesion = firstLesionResult(result);
        copyIfPresent(firstLesion, lesionModel, "mask_url");
        copyIfPresent(firstLesion, lesionModel, "preview_urls");
        copyIfPresent(firstLesion, lesionModel, "bbox");
        copyIfPresent(firstLesion, lesionModel, "affected_slices");
        copyIfPresent(firstLesion, lesionModel, "positive_voxel_count");
        copyIfPresent(firstLesion, lesionModel, "positive_voxel_ratio");
        copyIfPresent(firstLesion, lesionModel, "segmentation_runtime_status");
        copyIfPresent(firstLesion, lesionModel, "segmentation_checkpoint_provenance");
        aiStatus.put("lesion_model", lesionModel);
        return aiStatus;
    }

    private void copyIfPresent(Map<String, Object> source, Map<String, Object> target, String key) {
        Object value = source.get(key);
        if (value != null) {
            target.put(key, value);
        }
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

    private Double toDouble(Object value) {
        if (value instanceof Number number) {
            return number.doubleValue();
        }
        if (value != null) {
            try {
                return Double.parseDouble(value.toString());
            } catch (NumberFormatException ignored) {
                return null;
            }
        }
        return null;
    }

    private Integer toInteger(Object value, Integer fallback) {
        if (value instanceof Number number) {
            return number.intValue();
        }
        if (value != null) {
            try {
                return Integer.parseInt(value.toString());
            } catch (NumberFormatException ignored) {
                return fallback;
            }
        }
        return fallback;
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
