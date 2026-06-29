package com.neuedu.his.client;

import com.neuedu.his.config.HeadCtAiProperties;
import com.neuedu.his.exception.BusinessException;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.util.Map;

@Component
public class HeadCtClinicalAssistClient {
    private static final ParameterizedTypeReference<Map<String, Object>> MAP_TYPE =
            new ParameterizedTypeReference<>() {
            };

    private final RestClient restClient;
    private final HeadCtAiProperties properties;

    public HeadCtClinicalAssistClient(RestClient restClient, HeadCtAiProperties properties) {
        this.restClient = restClient;
        this.properties = properties;
    }

    public Map<String, Object> consultation(Map<String, Object> requestBody) {
        return post("/api/head-ct-ai/clinical/consultation", requestBody, "调用AI问诊RAG服务失败");
    }

    public Map<String, Object> diagnosis(Map<String, Object> requestBody) {
        return post("/api/head-ct-ai/clinical/diagnosis", requestBody, "调用AI辅助诊断RAG服务失败");
    }

    private Map<String, Object> post(String path, Map<String, Object> requestBody, String message) {
        try {
            return restClient.post()
                    .uri(resolveUrl(path))
                    .body(requestBody)
                    .retrieve()
                    .body(MAP_TYPE);
        } catch (RestClientException ex) {
            throw new BusinessException(502, message + ": " + ex.getMessage());
        }
    }

    private String resolveUrl(String path) {
        String base = properties.getOrchestratorBaseUrl();
        while (base.endsWith("/")) {
            base = base.substring(0, base.length() - 1);
        }
        return path.startsWith("/") ? base + path : base + "/" + path;
    }
}
