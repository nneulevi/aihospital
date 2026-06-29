package com.neuedu.his.service.impl;

import com.neuedu.his.model.dto.ImageAnalyzeRequestDTO;
import com.neuedu.his.model.dto.ImageUploadRequestDTO;
import com.neuedu.his.model.vo.ImageAnalyzeResponseVO;
import com.neuedu.his.service.ImageService;
import org.springframework.web.multipart.MultipartFile;

public class ImageServiceRealImpl implements ImageService {

    @Override
    public String upload(ImageUploadRequestDTO request, MultipartFile file) {
        throw new UnsupportedOperationException("真实AI模型待接入");
    }

    @Override
    public ImageAnalyzeResponseVO analyze(ImageAnalyzeRequestDTO request) {
        throw new UnsupportedOperationException("真实AI模型待接入");
    }
}