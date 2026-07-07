const fileInput = document.querySelector("#fileInput");
const dropzone = document.querySelector("#dropzone");
const fileName = document.querySelector("#fileName");
const submitBtn = document.querySelector("#submitBtn");
const backendSelect = document.querySelector("#backendSelect");
const modeSelect = document.querySelector("#modeSelect");
const serviceStatus = document.querySelector("#serviceStatus");
const progress = document.querySelector("#progress");
const logBox = document.querySelector("#logBox");
const healthBtn = document.querySelector("#healthBtn");
const downloadBtn = document.querySelector("#downloadBtn");

const fields = {
  status: document.querySelector("#mStatus"),
  voxels: document.querySelector("#mVoxels"),
  ratio: document.querySelector("#mRatio"),
  severity: document.querySelector("#mSeverity"),
  elapsed: document.querySelector("#mElapsed"),
  shape: document.querySelector("#mShape"),
  spacing: document.querySelector("#mSpacing"),
  maskFile: document.querySelector("#maskFile"),
  subtitle: document.querySelector("#resultSubtitle"),
};
const previews = {
  grid: document.querySelector("#previewGrid"),
  axial: document.querySelector("#previewAxial"),
  coronal: document.querySelector("#previewCoronal"),
  sagittal: document.querySelector("#previewSagittal"),
};

let selectedFile = null;

function backendBase() {
  const value = backendSelect.value;
  if (value === "same") return window.location.origin;
  return value.replace(/\/$/, "");
}

function formatLogData(message, data) {
  if (!data) return "";
  if (message === "服务状态") {
    const model = data.model || {};
    const inference = data.inference || {};
    return [
      `服务：${data.status === "ok" ? "运行正常" : "需要检查"}`,
      `模型：${model.available ? "已加载" : "未加载"}${data.model_name ? `（${data.model_name}）` : ""}`,
      model.device ? `设备：${model.device}` : "",
      data.model_version ? `版本：${data.model_version}` : "",
      inference.threshold !== undefined ? `阈值：${inference.threshold}` : "",
    ].filter(Boolean).join("\n");
  }
  if (message === "推理完成") {
    return [
      `状态：${data.status || "success"}`,
      `伪影比例：${((Number(data.artifact_ratio || 0)) * 100).toFixed(3)}%`,
      `严重程度：${data.severity || "-"}`,
      `阳性体素：${Number(data.positive_voxels || 0).toLocaleString()}`,
      data.elapsed_ms ? `耗时：${data.elapsed_ms} ms` : "",
    ].filter(Boolean).join("\n");
  }
  if (message === "任务已创建") {
    return `任务已进入队列：${data.task_id || "-"}\n状态：${data.status || "queued"}`;
  }
  if (data.error) {
    return `原因：${String(data.error)}`;
  }
  return String(data.message || "操作已记录。");
}

function log(message, data) {
  const time = new Date().toLocaleTimeString();
  const payload = data ? `\n${formatLogData(message, data)}` : "";
  logBox.textContent = `[${time}] ${message}${payload}\n\n${logBox.textContent}`;
}

function setStatus(ok, text) {
  serviceStatus.textContent = text;
  serviceStatus.classList.toggle("status-ok", ok);
  serviceStatus.classList.toggle("status-bad", !ok);
}

function setFile(file) {
  selectedFile = file;
  fileName.textContent = file ? file.name : "选择或拖入 NIfTI CT 文件";
  submitBtn.disabled = !file;
}

async function checkHealth() {
  try {
    const res = await fetch(`${backendBase()}/api/ct-artifact/health`);
    const data = await res.json();
    const ok = res.ok && data.model && data.model.available;
    setStatus(ok, ok ? "模型可用" : "模型异常");
    log("服务状态", data);
  } catch (err) {
    setStatus(false, "连接失败");
    log("服务状态检查失败", { error: String(err) });
  }
}

function renderResult(data) {
    const downloadUrl = `${backendBase()}${data.download_url}`;
    fields.status.textContent = data.status || "-";
    fields.voxels.textContent = Number(data.positive_voxels || 0).toLocaleString();
    fields.ratio.textContent = `${((Number(data.artifact_ratio || 0)) * 100).toFixed(3)}%`;
    fields.severity.textContent = data.severity || "-";
    fields.elapsed.textContent = data.elapsed_ms ? `${data.elapsed_ms} ms` : "-";
    fields.shape.textContent = (data.array_shape_zyx || data.shape || []).join(" x ");
    fields.spacing.textContent = (data.spacing || []).map((v) => Number(v).toFixed(3)).join(", ");
    fields.maskFile.textContent = data.mask_file || "-";
    fields.subtitle.textContent = data.backend ? `完成，后端：${data.backend}` : "完成，已生成 mask。";
    downloadBtn.href = downloadUrl;
    downloadBtn.classList.remove("disabled");
    if (data.preview_urls) {
      previews.axial.src = `${backendBase()}${data.preview_urls.axial}`;
      previews.coronal.src = `${backendBase()}${data.preview_urls.coronal}`;
      previews.sagittal.src = `${backendBase()}${data.preview_urls.sagittal}`;
      previews.grid.hidden = false;
    }
    log("推理完成", data);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function requestJson(url, options) {
  const res = await fetch(url, options);
  const data = await res.json();
  if (!res.ok) {
    const detail = data.detail || data;
    throw new Error(detail.message || detail.error_code || "服务处理失败");
  }
  return data;
}

async function submitSync(form) {
  const data = await requestJson(`${backendBase()}/api/ct-artifact/detect`, {
    method: "POST",
    body: form,
  });
  renderResult(data);
}

async function submitTask(form) {
  const task = await requestJson(`${backendBase()}/api/ct-artifact/tasks`, {
    method: "POST",
    body: form,
  });
  fields.status.textContent = task.status || "queued";
  fields.subtitle.textContent = `任务已创建：${task.task_id}`;
  log("任务已创建", task);

  let current = task;
  for (let i = 0; i < 120; i += 1) {
    await sleep(i === 0 ? 300 : 1000);
    current = await requestJson(`${backendBase()}${task.task_url}`);
    fields.status.textContent = current.status || "-";
    fields.elapsed.textContent = current.elapsed_ms ? `${current.elapsed_ms} ms` : "-";
    if (current.status === "success") {
      const result = await requestJson(`${backendBase()}${current.result_url}`);
      renderResult(result);
      return;
    }
    if (current.status === "failed") {
      throw new Error(current.error_message || current.error_code || "任务失败");
    }
  }
  throw new Error("任务轮询超时");
}

async function submitFile() {
  if (!selectedFile) return;
  const form = new FormData();
  form.append("file", selectedFile);
  submitBtn.disabled = true;
  progress.hidden = false;
  downloadBtn.classList.add("disabled");
  previews.grid.hidden = true;
  fields.subtitle.textContent = modeSelect.value === "task" ? "正在创建任务，请稍候。" : "正在上传并推理，请稍候。";

  try {
    if (modeSelect.value === "task") {
      await submitTask(form);
    } else {
      await submitSync(form);
    }
  } catch (err) {
    fields.status.textContent = "failed";
    fields.subtitle.textContent = "处理失败，请查看日志。";
    log("推理失败", { error: String(err) });
  } finally {
    progress.hidden = true;
    submitBtn.disabled = !selectedFile;
  }
}

fileInput.addEventListener("change", (event) => {
  setFile(event.target.files && event.target.files[0]);
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dragover");
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  const file = event.dataTransfer.files && event.dataTransfer.files[0];
  if (file) setFile(file);
});

submitBtn.addEventListener("click", submitFile);
healthBtn.addEventListener("click", checkHealth);
backendSelect.addEventListener("change", checkHealth);

checkHealth();
