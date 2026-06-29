# Spring Boot Client Example

以下示例展示主平台如何调用 `HeadCTOrchestrator`。代码仅示意调用流程，实际项目中可根据已有 HTTP 客户端封装调整。

## 1. 配置

```yaml
head-ct-ai:
  base-url: http://localhost:8010
  poll-interval-ms: 1000
  max-poll-count: 300
```

## 2. 创建任务

```java
RestTemplate restTemplate = new RestTemplate();

String baseUrl = "http://localhost:8010";
File ctFile = new File("D:/data/sample_ct.nii.gz");

MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
body.add("file", new FileSystemResource(ctFile));
body.add("patient_id", "patient_001");
body.add("study_id", "study_001");
body.add("series_id", "series_001");
body.add("report_id", "report_001");
body.add("doctor_id", "doctor_001");

HttpHeaders headers = new HttpHeaders();
headers.setContentType(MediaType.MULTIPART_FORM_DATA);

HttpEntity<MultiValueMap<String, Object>> request = new HttpEntity<>(body, headers);

ResponseEntity<Map> response = restTemplate.postForEntity(
    baseUrl + "/api/head-ct-ai/tasks",
    request,
    Map.class
);

Map task = response.getBody();
String taskId = (String) task.get("task_id");
String taskUrl = (String) task.get("task_url");
```

## 3. 轮询任务

```java
Map current = task;

for (int i = 0; i < 300; i++) {
    ResponseEntity<Map> taskResponse = restTemplate.getForEntity(
        baseUrl + taskUrl,
        Map.class
    );
    current = taskResponse.getBody();
    String status = (String) current.get("status");

    if ("success".equals(status)) {
        break;
    }

    if ("failed".equals(status)) {
        String errorCode = (String) current.get("error_code");
        String errorMessage = (String) current.get("error_message");
        throw new RuntimeException(errorCode + ": " + errorMessage);
    }

    Thread.sleep(1000);
}
```

## 4. 获取结果

```java
String resultUrl = (String) current.get("result_url");

ResponseEntity<Map> resultResponse = restTemplate.getForEntity(
    baseUrl + resultUrl,
    Map.class
);

Map result = resultResponse.getBody();

Map qualityControl = (Map) result.get("quality_control");
Map lesionAnalysis = (Map) result.get("lesion_analysis");
Map reportAssist = (Map) result.get("report_assist");

Boolean artifactDetected = (Boolean) qualityControl.get("artifact_detected");
String severity = (String) qualityControl.get("severity");
String summary = (String) reportAssist.get("summary");
```

## 5. 提交医生审核

```java
Map<String, Object> artifactReview = new HashMap<>();
artifactReview.put("accepted", true);
artifactReview.put("severity_override", null);
artifactReview.put("comment", "质控结果符合阅片感受。");

Map<String, Object> lesionReview = new HashMap<>();
lesionReview.put("accepted", true);
lesionReview.put("lesion_overrides", Collections.emptyList());
lesionReview.put("comment", "病灶识别结果仅作辅助参考。");

Map<String, Object> reportReview = new HashMap<>();
reportReview.put("ai_summary_used", true);
reportReview.put("final_report_text", "医生最终报告文本。");
reportReview.put("final_report_used", true);

Map<String, Object> safety = new HashMap<>();
safety.put("doctor_confirmed_ai_is_reference_only", true);
safety.put("requires_follow_up", false);

Map<String, Object> reviewRequest = new HashMap<>();
reviewRequest.put("review_status", "confirmed");
reviewRequest.put("doctor_id", "doctor_001");
reviewRequest.put("doctor_comment", "已结合原始影像复核。");
reviewRequest.put("artifact_review", artifactReview);
reviewRequest.put("lesion_review", lesionReview);
reviewRequest.put("report_review", reportReview);
reviewRequest.put("safety", safety);

ResponseEntity<Map> reviewResponse = restTemplate.postForEntity(
    baseUrl + "/api/head-ct-ai/reviews/" + taskId,
    reviewRequest,
    Map.class
);

Map review = (Map) reviewResponse.getBody().get("review");
```

## 6. 查询医生审核

```java
ResponseEntity<Map> reviewQueryResponse = restTemplate.getForEntity(
    baseUrl + "/api/head-ct-ai/reviews/" + taskId,
    Map.class
);

Map reviewQuery = (Map) reviewQueryResponse.getBody().get("review");
String reviewStatus = (String) reviewQuery.get("review_status");
```

如果任务存在但尚未审核，`review_status` 为 `pending`。

## 7. 平台建议处理

主平台建议保存：

- `task_id`
- `case_context`
- `quality_control`
- `lesion_analysis`
- `report_assist`
- `review`
- `warnings`
- `orchestrator_result.json` 原文
- `review.json` 原文

报告侧建议只把 `report_assist.summary` 作为草稿提示，不应自动写成最终诊断。

报告模块可以展示：

- `report_assist.suggested_report_sections`
- `report_assist.recommended_actions`
- `report_assist.rag_context.sources`
- `report_assist.llm_context.provider`
- `review.review_status`
- `review.report_review.final_report_text`

## 8. 错误处理

创建任务失败时：

```java
try {
    restTemplate.postForEntity(baseUrl + "/api/head-ct-ai/tasks", request, Map.class);
} catch (HttpClientErrorException | HttpServerErrorException ex) {
    Map error = new ObjectMapper().readValue(ex.getResponseBodyAsString(), Map.class);
    String errorCode = (String) error.get("error_code");
    String message = (String) error.get("message");
}
```

常见错误码：

```text
INVALID_FILE_TYPE
FILTER_UNAVAILABLE
FILTER_TASK_FAILED
FILTER_TIMEOUT
LESION_SERVICE_UNAVAILABLE
LESION_TASK_FAILED
LESION_TIMEOUT
TASK_NOT_FOUND
RESULT_NOT_FOUND
INVALID_REVIEW_PAYLOAD
INVALID_REVIEW_STATUS
TASK_NOT_SUCCESS
ORCHESTRATION_FAILED
```
