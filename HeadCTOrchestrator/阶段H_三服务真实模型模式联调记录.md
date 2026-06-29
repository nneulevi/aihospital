# 阶段 H：三服务真实模型模式联调记录

更新时间：2026-06-12

## 1. 本次联调范围

本次按“暂时略过正式训练 checkpoint”的策略推进阶段 H，只验证三服务技术链路：

```text
HeadCTOrchestrator
  -> Filter/Fastapi
  -> HeadCTLesionDetection LESION_MODE=model
  -> HeadCTOrchestrator 汇总结果
```

本次不进行模型质量验收，不输出准确率、AUC、敏感度、特异度等指标。

## 2. 使用的 checkpoint

```text
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/smoke_best.pt
```

类型：

```text
smoke_random_weights
```

用途：

```text
technical integration smoke test only
```

生成命令：

```powershell
python HeadCTLesionDetection/models/hemorrhage/create_smoke_checkpoint.py `
  --output HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/smoke_best.pt `
  --base-channels 2 `
  --input-shape 16,64,64
```

说明：

- 该 checkpoint 为随机权重。
- 只用于验证 `LESION_MODE=model` 的加载、推理和 API 链路。
- 不能用于模型质量验收或临床结论。

## 3. 已补充内容

新增：

```text
HeadCTLesionDetection/models/hemorrhage/create_smoke_checkpoint.py
```

更新：

```text
HeadCTOrchestrator/OrchestratorServer.py
HeadCTOrchestrator/tests/test_orchestrator_pipeline.py
HeadCTOrchestrator/阶段H_三服务真实模型模式联调详细指导.md
HeadCTOrchestrator/下一步开发指导.md
```

## 4. 自动化验证

执行命令：

```powershell
python -m pytest HeadCTOrchestrator/tests/test_orchestrator_pipeline.py -q
```

结果：

```text
9 passed
```

覆盖场景：

- Orchestrator health。
- Orchestrator + Filter 基础链路。
- Orchestrator + Filter + LesionDetection mock 链路。
- Orchestrator + Filter + LesionDetection model 链路。
- model 链路使用 `smoke_best.pt`。
- Filter 不可用时返回 `FILTER_UNAVAILABLE`。
- LesionDetection 不可用时返回 `LESION_SERVICE_UNAVAILABLE`。
- checkpoint 缺失时返回 `LESION_TASK_FAILED`，并保留下游 `MODEL_CHECKPOINT_NOT_FOUND` 信息。
- 非 NIfTI 文件返回 `INVALID_FILE_TYPE`。
- 任务和结果不存在时返回稳定错误码。

## 5. 当前验收结论

阶段 H 的技术联调已具备自动化验证能力。

当前可认为完成：

- 三服务合同链路验证。
- `LESION_MODE=model` 加载 checkpoint 的工程路径验证。
- Orchestrator 汇总 `lesion_analysis.status=success` 的路径验证。
- 下游服务不可用和 checkpoint 缺失的错误码验证。

当前未完成：

- 真实训练 checkpoint 质量验收。
- `metrics.json` 和 `predictions.csv` 正式模型评估结果。
- 真实数据集上的临床或科研指标分析。

## 6. 下一步

后续恢复阶段 G 时，应替换为真实训练得到的：

```text
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/best.pt
```

并补充：

```text
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/metrics.json
HeadCTLesionDetection/models/hemorrhage/runs/hemorrhage_v1/eval/predictions.csv
```

真实模型完成后，应重新执行阶段 H 联调，并更新本记录。
