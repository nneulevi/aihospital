package com.neuedu.his.service.impl;

import com.neuedu.his.mapper.AiImageAnalysisMapper;
import com.neuedu.his.mapper.AiImageFileMapper;
import com.neuedu.his.model.dto.ImageAnalyzeRequestDTO;
import com.neuedu.his.model.dto.ImageUploadRequestDTO;
import com.neuedu.his.model.entity.AiImageAnalysis;
import com.neuedu.his.model.entity.AiImageFile;
import com.neuedu.his.model.vo.ImageAnalyzeResponseVO;
import com.neuedu.his.service.ImageService;
import com.neuedu.his.util.FileUploadUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Primary;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
@Service          // ← 添加这个
@Primary          // ← 添加这个
public class ImageServiceMockImpl implements ImageService {

    @Autowired
    private AiImageAnalysisMapper aiImageAnalysisMapper;

    @Autowired
    private AiImageFileMapper aiImageFileMapper;

    @Override
    public String upload(ImageUploadRequestDTO request, MultipartFile file) {
        String filePath = FileUploadUtil.save(file, "ct/" + request.getRegisterId());

        AiImageFile imageFile = new AiImageFile();
        imageFile.setCheckRequestId(request.getCheckRequestId());
        imageFile.setRegisterId(request.getRegisterId());
        imageFile.setFilePath(filePath);
        imageFile.setFileName(file.getOriginalFilename());
        imageFile.setFileSize(file.getSize());
        imageFile.setFileFormat(file.getContentType());
        imageFile.setUploadBy(0);
        aiImageFileMapper.insert(imageFile);

        return filePath;
    }

    @Override
    public ImageAnalyzeResponseVO analyze(ImageAnalyzeRequestDTO request) {
        List<ImageAnalyzeResponseVO.Annotation> annotations = new ArrayList<>();

        ImageAnalyzeResponseVO.Annotation anno = new ImageAnalyzeResponseVO.Annotation();
        anno.setX(120);
        anno.setY(80);
        anno.setWidth(45);
        anno.setHeight(30);
        anno.setLabel("疑似低密度影");
        annotations.add(anno);

        AiImageAnalysis analysis = new AiImageAnalysis();
        analysis.setCheckRequestId(request.getCheckRequestId());
        analysis.setFilePath("/storage/ct/mock.jpg");
        analysis.setAiFindings("右侧颞叶见片状低密度影，边界欠清，CT值约18-22Hu");
        analysis.setAiAnnotation("{\"annotations\":[{\"x\":120,\"y\":80,\"w\":45,\"h\":30,\"label\":\"低密度影\"}]}");
        analysis.setAiConclusion("考虑脑梗死早期改变，建议MRI进一步检查");
        analysis.setConfidence(BigDecimal.valueOf(0.87));
        analysis.setAiModelVersion("Mock-CT-v1.0");
        aiImageAnalysisMapper.insert(analysis);

        ImageAnalyzeResponseVO response = new ImageAnalyzeResponseVO();
        response.setAnalysisId(analysis.getId());
        response.setFindings(analysis.getAiFindings());
        response.setConclusion(analysis.getAiConclusion());
        response.setConfidence(0.87);
        response.setAnnotations(annotations);
        return response;
    }
}