package com.neuedu.his.controller;

import com.neuedu.his.model.dto.ImageAnalyzeRequestDTO;
import com.neuedu.his.model.dto.ImageUploadRequestDTO;
import com.neuedu.his.model.vo.ImageAnalyzeResponseVO;
import com.neuedu.his.service.ImageService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

@RestController
@RequestMapping("/api/ai/image")
public class AiImageController {

    @Autowired
    private ImageService imageService;

    @PostMapping("/upload")
    public String upload(@RequestParam("file") MultipartFile file,
                         @RequestParam("checkRequestId") Integer checkRequestId,
                         @RequestParam("registerId") Integer registerId) {
        ImageUploadRequestDTO request = new ImageUploadRequestDTO();
        request.setCheckRequestId(checkRequestId);
        request.setRegisterId(registerId);
        return imageService.upload(request, file);
    }

    @PostMapping("/analyze")
    public ImageAnalyzeResponseVO analyze(@RequestBody @Valid ImageAnalyzeRequestDTO request) {
        return imageService.analyze(request);
    }
}