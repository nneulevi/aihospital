package com.neuedu.his.client;

import com.neuedu.his.config.HeadCtAiProperties;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.util.JsonUtil;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.StringReader;
import java.net.HttpURLConnection;
import java.net.URI;
import java.nio.charset.StandardCharsets;
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

    public void streamConsultation(Map<String, Object> requestBody, ClinicalSseEventHandler handler) {
        stream("/api/head-ct-ai/clinical/consultation/stream", requestBody, handler, "调用AI问诊流式RAG服务失败");
    }

    public void streamDiagnosis(Map<String, Object> requestBody, ClinicalSseEventHandler handler) {
        stream("/api/head-ct-ai/clinical/diagnosis/stream", requestBody, handler, "调用AI辅助诊断流式RAG服务失败");
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

    private void stream(String path, Map<String, Object> requestBody, ClinicalSseEventHandler handler, String message) {
        HttpURLConnection connection = null;
        try {
            connection = (HttpURLConnection) URI.create(resolveUrl(path)).toURL().openConnection();
            connection.setRequestMethod("POST");
            int timeoutMillis = (int) properties.getRequestTimeoutSeconds() * 1000;
            connection.setConnectTimeout(timeoutMillis);
            connection.setReadTimeout(timeoutMillis);
            connection.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            connection.setRequestProperty("Accept", "text/event-stream");
            connection.setDoOutput(true);
            try (OutputStream outputStream = connection.getOutputStream()) {
                outputStream.write(JsonUtil.toJson(requestBody).getBytes(StandardCharsets.UTF_8));
            }
            int status = connection.getResponseCode();
            if (status < 200 || status >= 300) {
                String error = "";
                if (connection.getErrorStream() != null) {
                    error = readAll(new String(connection.getErrorStream().readAllBytes(), StandardCharsets.UTF_8));
                }
                throw new BusinessException(502, message + ": upstream status " + status + " " + error);
            }
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream(), StandardCharsets.UTF_8))) {
                dispatchSse(reader, handler);
            }
        } catch (IOException | RuntimeException ex) {
            if (ex instanceof BusinessException businessException) {
                throw businessException;
            }
            throw new BusinessException(502, message + ": " + ex.getMessage());
        } finally {
            if (connection != null) {
                connection.disconnect();
            }
        }
    }

    private void dispatchSse(BufferedReader reader, ClinicalSseEventHandler handler) throws IOException {
        String event = "message";
        StringBuilder data = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            if (line.isEmpty()) {
                if (!data.isEmpty()) {
                    handler.onEvent(event, data.toString());
                }
                event = "message";
                data.setLength(0);
            } else if (line.startsWith("event:")) {
                event = line.substring(6).trim();
            } else if (line.startsWith("data:")) {
                if (!data.isEmpty()) {
                    data.append('\n');
                }
                data.append(line.substring(5).trim());
            }
        }
        if (!data.isEmpty()) {
            handler.onEvent(event, data.toString());
        }
    }

    private String readAll(String text) throws IOException {
        try (BufferedReader reader = new BufferedReader(new StringReader(text))) {
            StringBuilder builder = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
            return builder.toString();
        }
    }

    private String resolveUrl(String path) {
        String base = properties.getOrchestratorBaseUrl();
        while (base.endsWith("/")) {
            base = base.substring(0, base.length() - 1);
        }
        return path.startsWith("/") ? base + path : base + "/" + path;
    }

    @FunctionalInterface
    public interface ClinicalSseEventHandler {
        void onEvent(String event, String data) throws IOException;
    }
}
