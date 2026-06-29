package com.neuedu.his.service;

import com.neuedu.his.client.HeadCtOrchestratorClient;
import com.neuedu.his.client.HeadCtReportClient;
import com.neuedu.his.config.HeadCtAiProperties;
import com.neuedu.his.exception.BusinessException;
import com.neuedu.his.model.entity.AiImageFile;
import com.neuedu.his.model.entity.CheckRequest;
import com.neuedu.his.model.entity.Register;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;

@Service
public class HeadCtAiWorkflowService {
    private final HeadCtOrchestratorClient orchestratorClient;
    private final HeadCtReportClient reportClient;
    private final HeadCtAiProperties properties;

    public HeadCtAiWorkflowService(HeadCtOrchestratorClient orchestratorClient,
                                   HeadCtReportClient reportClient,
                                   HeadCtAiProperties properties) {
        this.orchestratorClient = orchestratorClient;
        this.reportClient = reportClient;
        this.properties = properties;
    }

    public Map<String, Object> createAndWaitAnalysis(AiImageFile imageFile,
                                                     CheckRequest checkRequest,
                                                     Register register) {
        Path filePath = resolveUploadedFile(imageFile.getFilePath());
        String patientId = buildPatientId(register, checkRequest);
        String studyId = buildStudyId(checkRequest);
        String seriesId = "IMAGE-" + imageFile.getId();
        String reportId = "CHECK-" + checkRequest.getId();
        String doctorId = buildDoctorId(register);

        Map<String, Object> task = orchestratorClient.createTask(
                filePath, patientId, studyId, seriesId, reportId, doctorId
        );

        String taskId = asString(task.get("task_id"));
        if (!StringUtils.hasText(taskId)) {
            throw new BusinessException(502, "头部CT AI编排服务未返回task_id");
        }

        Map<String, Object> latestTask = waitUntilFinished(task);
        String status = asString(latestTask.get("status"));
        if (!isSuccessStatus(status)) {
            throw new BusinessException(502, "头部CT AI任务未成功完成，当前状态: " + status);
        }

        String resultUrl = firstText(latestTask.get("result_url"), task.get("result_url"));
        if (!StringUtils.hasText(resultUrl)) {
            resultUrl = "/api/head-ct-ai/results/" + taskId;
        }

        Map<String, Object> result = orchestratorClient.getResult(resultUrl);
        result.putIfAbsent("task_id", taskId);
        result.putIfAbsent("task_status", status);
        result.putIfAbsent("task_snapshot", latestTask);
        return result;
    }

    public Map<String, Object> createReportDraft(String taskId,
                                                 CheckRequest checkRequest,
                                                 Register register,
                                                 String reportType) {
        Map<String, Object> body = new LinkedHashMap<>();
        body.put("order_id", buildStudyId(checkRequest));
        body.put("study_id", buildStudyId(checkRequest));
        body.put("patient_id", buildPatientId(register, checkRequest));
        body.put("accession_number", "ACC-CHECK-" + checkRequest.getId());
        body.put("department", "门诊");
        body.put("ordering_doctor_id", buildDoctorId(register));
        body.put("assigned_doctor_id", buildDoctorId(register));
        body.put("report_type", reportType);

        String requestId = "project2-report-" + checkRequest.getId() + "-" + taskId;
        return reportClient.createReportFromAnalysis(taskId, body, requestId);
    }

    public String buildStudyId(CheckRequest checkRequest) {
        return "CHECK-" + checkRequest.getId();
    }

    public String buildPatientId(Register register, CheckRequest checkRequest) {
        if (register != null && register.getPatientId() != null) {
            return "PATIENT-" + register.getPatientId();
        }
        return "REGISTER-" + checkRequest.getRegisterId();
    }

    public String buildDoctorId(Register register) {
        if (register != null && register.getEmployeeId() != null) {
            return "DOCTOR-" + register.getEmployeeId();
        }
        return properties.getActorId();
    }

    private Map<String, Object> waitUntilFinished(Map<String, Object> initialTask) {
        Map<String, Object> latestTask = initialTask;
        String taskId = asString(initialTask.get("task_id"));
        String taskUrl = firstText(initialTask.get("task_url"), "/api/head-ct-ai/tasks/" + taskId);
        Instant deadline = Instant.now().plus(Duration.ofSeconds(properties.getTimeoutSeconds()));

        while (Instant.now().isBefore(deadline)) {
            String status = asString(latestTask.get("status"));
            if (isSuccessStatus(status) || isFailureStatus(status)) {
                return latestTask;
            }

            try {
                Thread.sleep(properties.getPollIntervalMs());
            } catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
                throw new BusinessException(500, "等待头部CT AI任务时被中断");
            }

            latestTask = orchestratorClient.getTask(taskUrl);
        }

        throw new BusinessException(504, "等待头部CT AI任务超时");
    }

    private Path resolveUploadedFile(String storedPath) {
        if (!StringUtils.hasText(storedPath)) {
            throw new BusinessException("影像文件路径为空");
        }
        String normalized = storedPath.startsWith("/") ? storedPath.substring(1) : storedPath;
        Path path = Paths.get(normalized).toAbsolutePath().normalize();
        if (!Files.exists(path)) {
            throw new BusinessException("影像文件不存在: " + path);
        }
        return path;
    }

    private boolean isSuccessStatus(String status) {
        String value = normalizeStatus(status);
        return "success".equals(value) || "succeeded".equals(value) || "completed".equals(value) || "done".equals(value);
    }

    private boolean isFailureStatus(String status) {
        String value = normalizeStatus(status);
        return "failed".equals(value) || "error".equals(value) || "cancelled".equals(value) || "canceled".equals(value);
    }

    private String normalizeStatus(String status) {
        return status == null ? "" : status.trim().toLowerCase();
    }

    private String firstText(Object... values) {
        for (Object value : values) {
            String text = asString(value);
            if (StringUtils.hasText(text)) {
                return text;
            }
        }
        return null;
    }

    private String asString(Object value) {
        return Objects.toString(value, null);
    }
}
