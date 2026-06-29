package com.neuedu.his.util;

import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.UUID;

public class FileUploadUtil {
    private static final String[] ALLOWED_EXTENSIONS = {
            "jpg", "jpeg", "png", "gif", "pdf",
            "nii", "nii.gz", "dcm", "dicom", "zip", "mha", "mhd", "nrrd"
    };

    public static String uploadFile(byte[] fileBytes, String fileName, String uploadDir) throws IOException {
        String extension = getFileExtension(fileName);
        if (!isAllowedExtension(extension)) {
            throw new IllegalArgumentException("不支持的文件类型");
        }

        String newFileName = UUID.randomUUID() + "." + extension;
        File dir = new File(uploadDir);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        Path filePath = Paths.get(uploadDir, newFileName);
        Files.write(filePath, fileBytes);

        return newFileName;
    }

    public static String save(MultipartFile file, String relativePath) {
        try {
            String uploadDir = "uploads/" + relativePath;
            String extension = getFileExtension(file.getOriginalFilename());
            if (!isAllowedExtension(extension)) {
                throw new IllegalArgumentException("不支持的文件类型");
            }

            String newFileName = UUID.randomUUID() + "." + extension;
            File dir = new File(uploadDir);
            if (!dir.exists()) {
                dir.mkdirs();
            }

            Path filePath = Paths.get(uploadDir, newFileName);
            Files.write(filePath, file.getBytes());

            return "/uploads/" + relativePath + "/" + newFileName;
        } catch (IOException e) {
            throw new RuntimeException("文件保存失败", e);
        }
    }

    private static String getFileExtension(String fileName) {
        if (fileName == null || !fileName.contains(".")) {
            return "";
        }
        String lowerName = fileName.toLowerCase();
        if (lowerName.endsWith(".nii.gz")) {
            return "nii.gz";
        }
        return lowerName.substring(lowerName.lastIndexOf(".") + 1);
    }

    private static boolean isAllowedExtension(String extension) {
        for (String allowed : ALLOWED_EXTENSIONS) {
            if (allowed.equalsIgnoreCase(extension)) {
                return true;
            }
        }
        return false;
    }
}
