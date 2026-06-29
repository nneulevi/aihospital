package com.neuedu.his.service;

import com.neuedu.his.model.dto.ImageAnalyzeRequestDTO;
import com.neuedu.his.model.dto.ImageUploadRequestDTO;
import com.neuedu.his.model.vo.ImageAnalyzeResponseVO;
import org.springframework.web.multipart.MultipartFile;

public interface ImageService {
    String upload(ImageUploadRequestDTO request, MultipartFile file);
    ImageAnalyzeResponseVO analyze(ImageAnalyzeRequestDTO request);
}