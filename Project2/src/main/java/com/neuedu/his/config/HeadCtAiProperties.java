package com.neuedu.his.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "ai.head-ct")
public class HeadCtAiProperties {
    private String orchestratorBaseUrl = "http://127.0.0.1:8010";
    private String reportBaseUrl = "http://127.0.0.1:8030";
    private long pollIntervalMs = 1000;
    private long timeoutSeconds = 300;
    private long requestTimeoutSeconds = 30;
    private String actorId = "project2-platform";
    private String actorRole = "integration_service";
}
