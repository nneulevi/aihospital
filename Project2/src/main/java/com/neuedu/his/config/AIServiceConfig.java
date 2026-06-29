package com.neuedu.his.config;

import com.neuedu.his.service.*;
import com.neuedu.his.service.impl.*;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;

@Configuration
@EnableConfigurationProperties(HeadCtAiProperties.class)
public class AIServiceConfig {

    @Bean
    public RestClient restClient(RestClient.Builder builder, HeadCtAiProperties properties) {
        SimpleClientHttpRequestFactory requestFactory = new SimpleClientHttpRequestFactory();
        Duration timeout = Duration.ofSeconds(properties.getRequestTimeoutSeconds());
        requestFactory.setConnectTimeout(timeout);
        requestFactory.setReadTimeout(timeout);
        return builder.requestFactory(requestFactory).build();
    }

    // ConsultationService
    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "true", matchIfMissing = true)
    public ConsultationService consultationServiceMock() {
        return new ConsultationServiceMockImpl();
    }

    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "false")
    public ConsultationService consultationServiceReal() {
        return new ConsultationServiceRealImpl();
    }

    // DiagnosisService
    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "true", matchIfMissing = true)
    public DiagnosisService diagnosisServiceMock() {
        return new DiagnosisServiceMockImpl();
    }

    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "false")
    public DiagnosisService diagnosisServiceReal() {
        return new DiagnosisServiceRealImpl();
    }

    // ReportService
    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "true", matchIfMissing = true)
    public ReportService reportServiceMock() {
        return new ReportServiceMockImpl();
    }

    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "false")
    public ReportService reportServiceReal() {
        return new ReportServiceRealImpl();
    }

    // ImageService
    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "true", matchIfMissing = true)
    public ImageService imageServiceMock() {
        return new ImageServiceMockImpl();
    }

    @Bean
    @ConditionalOnProperty(name = "ai.mock.enabled", havingValue = "false")
    public ImageService imageServiceReal() {
        return new ImageServiceRealImpl();
    }
}
