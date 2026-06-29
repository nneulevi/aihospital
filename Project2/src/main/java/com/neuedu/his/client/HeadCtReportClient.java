package com.neuedu.his.client;

import com.neuedu.his.config.HeadCtAiProperties;
import com.neuedu.his.exception.BusinessException;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.Map;

@Component
public class HeadCtReportClient {
    private static final ParameterizedTypeReference<Map<String, Object>> MAP_TYPE =
            new ParameterizedTypeReference<>() {
            };

    private final RestClient restClient;
    private final HeadCtAiProperties properties;

    public HeadCtReportClient(RestClient restClient, HeadCtAiProperties properties) {
        this.restClient = restClient;
        this.properties = properties;
    }

    public Map<String, Object> createReportFromAnalysis(String taskId,
                                                        Map<String, Object> requestBody,
                                                        String requestId) {
        try {
            return restClient.post()
                    .uri(resolveUrl("/api/v1/reports/from-analysis/" + taskId))
                    .header("X-Actor-Id", properties.getActorId())
                    .header("X-Actor-Role", properties.getActorRole())
                    .header("X-Request-Id", requestId)
                    .header("Idempotency-Key", requestId)
                    .body(requestBody)
                    .retrieve()
                    .body(MAP_TYPE);
        } catch (RestClientException ex) {
            throw new BusinessException(502, "调用头部CT报告服务失败: " + ex.getMessage());
        }
    }

    private String resolveUrl(String url) {
        String base = trimTrailingSlash(properties.getReportBaseUrl());
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
