package com.neuedu.his.client;

import com.neuedu.his.config.HeadCtAiProperties;
import com.neuedu.his.exception.BusinessException;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.core.io.FileSystemResource;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.util.StringUtils;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.nio.file.Path;
import java.util.Map;

@Component
public class HeadCtOrchestratorClient {
    private static final ParameterizedTypeReference<Map<String, Object>> MAP_TYPE =
            new ParameterizedTypeReference<>() {
            };

    private final RestClient restClient;
    private final HeadCtAiProperties properties;

    public HeadCtOrchestratorClient(RestClient restClient, HeadCtAiProperties properties) {
        this.restClient = restClient;
        this.properties = properties;
    }

    public Map<String, Object> createTask(Path filePath,
                                          String patientId,
                                          String studyId,
                                          String seriesId,
                                          String reportId,
                                          String doctorId) {
        MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
        body.add("file", new FileSystemResource(filePath));
        addTextPart(body, "patient_id", patientId);
        addTextPart(body, "study_id", studyId);
        addTextPart(body, "series_id", seriesId);
        addTextPart(body, "report_id", reportId);
        addTextPart(body, "doctor_id", doctorId);

        try {
            return restClient.post()
                    .uri(resolveUrl("/api/head-ct-ai/tasks"))
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .body(body)
                    .retrieve()
                    .body(MAP_TYPE);
        } catch (RestClientException ex) {
            throw new BusinessException(502, "调用头部CT AI编排服务失败: " + ex.getMessage());
        }
    }

    public Map<String, Object> getTask(String taskUrl) {
        return getMap(taskUrl, "查询头部CT AI任务失败");
    }

    public Map<String, Object> getResult(String resultUrl) {
        return getMap(resultUrl, "获取头部CT AI结果失败");
    }

    private Map<String, Object> getMap(String url, String message) {
        try {
            return restClient.get()
                    .uri(resolveUrl(url))
                    .retrieve()
                    .body(MAP_TYPE);
        } catch (RestClientException ex) {
            throw new BusinessException(502, message + ": " + ex.getMessage());
        }
    }

    private void addTextPart(MultiValueMap<String, Object> body, String name, String value) {
        if (StringUtils.hasText(value)) {
            body.add(name, value);
        }
    }

    private String resolveUrl(String url) {
        if (url == null || url.isBlank()) {
            throw new BusinessException("AI服务返回的URL为空");
        }
        if (url.startsWith("http://") || url.startsWith("https://")) {
            return url;
        }
        String base = trimTrailingSlash(properties.getOrchestratorBaseUrl());
        return url.startsWith("/") ? base + url : base + "/" + url;
    }

    private String trimTrailingSlash(String value) {
        if (value == null) {
            return "";
        }
        while (value.endsWith("/")) {
            value = value.substring(0, value.length() - 1);
        }
        return value;
    }
}
