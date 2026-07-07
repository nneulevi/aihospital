const state = { reports: [], current: null, activeTab: "ai" };
const $ = (id) => document.getElementById(id);
const query = new URLSearchParams(window.location.search);
const statusNames = {
  draft: "草稿", pending_review: "待审核", revision_required: "待修订",
  approved: "已通过", signed: "已签署", released: "已发布", amendment_draft: "补充报告草稿"
};

function headers(json = false) {
  const value = {
    "X-Actor-Id": $("actorId").value.trim(),
    "X-Actor-Role": $("actorRole").value
  };
  if (json) value["Content-Type"] = "application/json";
  return value;
}

async function api(path, options = {}) {
  const response = await fetch(path, { ...options, headers: { ...headers(Boolean(options.body)), ...(options.headers || {}) } });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.error?.message || `请求失败 (${response.status})`);
  return payload;
}

function toast(message, error = false) {
  const node = $("toast");
  node.textContent = message;
  node.className = `toast show${error ? " error" : ""}`;
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => { node.className = "toast"; }, 2600);
}

async function loadHealth() {
  try {
    const health = await fetch("/api/v1/health").then((r) => r.json());
    $("serviceStatus").textContent = `报告服务 ${health.status} · 数据库 ${health.database.status}`;
  } catch (_) {
    $("serviceStatus").textContent = "报告服务不可用";
  }
}

async function loadReports(keepSelection = true) {
  const query = new URLSearchParams();
  if ($("statusFilter").value) query.set("status", $("statusFilter").value);
  const payload = await api(`/api/v1/reports?${query.toString()}`);
  state.reports = payload.reports;
  $("reportCount").textContent = `${payload.count} 项`;
  renderList();
  if (keepSelection && state.current) {
    const updated = state.reports.find((item) => item.id === state.current.id);
    if (updated) selectReport(updated.id);
  }
}

function renderList() {
  const list = $("reportList");
  list.innerHTML = "";
  state.reports.forEach((report) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `report-item${state.current?.id === report.id ? " active" : ""}`;
    button.innerHTML = `
      <span class="report-item-row"><strong>${escapeHtml(report.accession_number || report.study_id)}</strong><span class="mini-status">${statusNames[report.status] || report.status}</span></span>
      <span>${escapeHtml(report.patient_id)} · ${escapeHtml(report.department || "未分配科室")}</span>
      <small>版本 ${report.version_number} · ${formatTime(report.updated_at)}</small>`;
    button.addEventListener("click", () => selectReport(report.id));
    list.appendChild(button);
  });
}

async function selectReport(reportId) {
  const payload = await api(`/api/v1/reports/${reportId}`);
  state.current = payload.report;
  renderList();
  renderReport();
  renderTab();
}

function renderReport() {
  const r = state.current;
  $("emptyState").hidden = true;
  $("reportContent").hidden = false;
  $("accessionLabel").textContent = r.accession_number || r.study_id;
  $("patientTitle").textContent = `患者 ${r.patient_id}`;
  const emrText = r.external_document_id ? ` · EMR ${r.external_document_id}` : " · EMR 未归档";
  $("studyMeta").textContent = `${r.department || "未分配科室"} · 检查 ${r.study_id} · 版本 ${r.version_number}${emrText}`;
  $("statusBadge").textContent = statusNames[r.status] || r.status;
  $("deploymentBadge").textContent = r.deployment_mode === "production" ? "生产环境" : `${r.deployment_mode} 环境`;
  $("findings").value = r.findings || "";
  $("impression").value = r.impression || "";
  $("recommendations").value = r.recommendations || "";
  const editable = ["draft", "revision_required", "amendment_draft"].includes(r.status);
  ["findings", "impression", "recommendations"].forEach((id) => { $(id).disabled = !editable; });
  $("saveButton").disabled = !editable;
  $("submitButton").disabled = !editable;
  $("approveButton").disabled = r.status !== "pending_review";
  $("revisionButton").disabled = r.status !== "pending_review";
  $("signButton").disabled = r.status !== "approved";
  $("releaseButton").disabled = r.status !== "signed";
}

async function action(path, method = "POST", body = null) {
  if (!state.current) return;
  try {
    const payload = await api(`/api/v1/reports/${state.current.id}/${path}`, {
      method,
      body: body ? JSON.stringify(body) : undefined,
      headers: path === "sign" ? { "X-Signature-Confirmation": "confirm" } : {}
    });
    state.current = payload.report;
    toast("操作已完成");
    await loadReports(true);
  } catch (error) { toast(error.message, true); }
}

async function saveDraft() {
  await action("draft", "PATCH", {
    findings: $("findings").value,
    impression: $("impression").value,
    recommendations: $("recommendations").value,
    expected_version: state.current.version_lock,
    change_reason: "医生工作台编辑"
  });
}

function applyEmbeddedIdentity() {
  const actorId = query.get("actorId");
  const actorRole = query.get("actorRole");
  if (actorId && $("actorId")) $("actorId").value = actorId;
  if (actorRole && $("actorRole")) $("actorRole").value = actorRole;
}

function asObject(value) {
  if (!value) return {};
  if (typeof value === "string") {
    try { return JSON.parse(value); } catch (_) { return {}; }
  }
  return typeof value === "object" ? value : {};
}

function asArray(value) {
  if (!value) return [];
  return Array.isArray(value) ? value : [value];
}

function firstValue(source, names, fallback = "") {
  const object = asObject(source);
  for (const name of names) {
    if (object[name] !== undefined && object[name] !== null && object[name] !== "") return object[name];
  }
  return fallback;
}

function formatPercent(value, digits = 1) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "-";
  const percent = number <= 1 ? number * 100 : number;
  return `${Math.max(0, Math.min(100, percent)).toFixed(digits)}%`;
}

function formatNumber(value, digits = 3) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "-";
}

function formatSliceList(value) {
  const rows = asArray(value).map((item) => String(item ?? "").trim()).filter(Boolean);
  return rows.length ? rows.join("、") : "未明确";
}

function formatAiWorkflowLabel(value) {
  const object = asObject(value);
  const hasQuality = Boolean(object.quality_control || object.qualityControl || object.filter);
  const hasLesion = Boolean(object.lesion || object.lesion_model || object.lesionModel);
  const labels = [];
  if (hasQuality) labels.push("图像质控");
  if (hasLesion) labels.push("病灶识别");
  labels.push("报告辅助");
  return `${labels.join("、")}已完成`;
}

function severityLabel(value) {
  const map = { none: "未见明确伪影", mild: "轻度", moderate: "中度", severe: "重度", unknown: "未明确" };
  return map[String(value || "unknown")] || String(value || "未明确");
}

function boolLabel(value) {
  if (value === true) return "是";
  if (value === false) return "否";
  return "未明确";
}

function summaryCard(title, value, note = "") {
  return `
    <div class="summary-card">
      <span>${escapeHtml(title)}</span>
      <strong>${escapeHtml(value)}</strong>
      ${note ? `<small>${escapeHtml(note)}</small>` : ""}
    </div>`;
}

function confidenceMeter(label, value) {
  const number = Number(value);
  const hasValue = Number.isFinite(number);
  const percent = hasValue ? Math.max(0, Math.min(100, number <= 1 ? number * 100 : number)) : 0;
  return `
    <div class="confidence-row">
      <span>${escapeHtml(label)}</span>
      <div class="confidence-meter" aria-label="${escapeHtml(label)} ${percent.toFixed(0)}%">
        <div style="width: ${percent.toFixed(0)}%"></div>
      </div>
      <strong>${hasValue ? `${percent.toFixed(1)}%` : "未返回"}</strong>
    </div>`;
}

function listBlock(title, items) {
  const rows = asArray(items).map((item) => String(item || "").trim()).filter(Boolean);
  if (!rows.length) return "";
  return `
    <section class="ai-section">
      <h3>${escapeHtml(title)}</h3>
      <ul>${rows.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
    </section>`;
}

function renderPreviewImages(previewUrls) {
  const labels = { axial: "轴位", coronal: "冠状位", sagittal: "矢状位" };
  const urls = asObject(previewUrls);
  const entries = Object.entries(labels).filter(([key]) => urls[key]);
  if (!entries.length) return "";
  return `
    <section class="ai-section">
      <h3>影像可视化输出</h3>
      <div class="preview-grid">
        ${entries.map(([key, label]) => `
          <figure class="preview-card">
            <img src="${escapeHtml(urls[key])}" alt="${escapeHtml(label)}预览图">
            <figcaption>${escapeHtml(label)}</figcaption>
          </figure>`).join("")}
      </div>
    </section>`;
}

function renderAiInterpretation() {
  const qc = asObject(state.current.quality_control_json);
  const lesion = asObject(state.current.lesion_analysis_json);
  const modelVersions = asObject(state.current.model_versions);
  const results = asArray(firstValue(lesion, ["results"], []));
  const primaryLesion = results[0] || {};
  const severity = firstValue(qc, ["severity"], "unknown");
  const artifactRatio = firstValue(qc, ["artifact_ratio", "artifactRatio"], null);
  const affectedSlices = asArray(firstValue(qc, ["affected_slices", "affectedSlices"], []));
  const artifactDetected = firstValue(qc, ["artifact_detected", "artifactDetected"], null);
  const positiveProbability = firstValue(primaryLesion, ["positive_probability", "positiveProbability", "probability"], firstValue(lesion, ["positive_probability", "positiveProbability"], null));
  const lesionStatus = firstValue(lesion, ["status"], "unknown");
  const reportSuggestion = firstValue(primaryLesion, ["report_suggestion", "reportSuggestion"], firstValue(lesion, ["report_suggestion", "reportSuggestion"], ""));
  const reviewFocus = firstValue(lesion, ["review_focus", "reviewFocus"], []);
  const warnings = [
    ...asArray(firstValue(qc, ["warnings"], [])),
    ...asArray(firstValue(lesion, ["warnings"], [])),
  ];
  const limitations = [
    ...asArray(firstValue(qc, ["limitations"], [])),
    ...asArray(firstValue(lesion, ["limitations"], [])),
  ];
  const previewUrls = firstValue(qc, ["preview_urls", "previewUrls"], {});

  const artifactText = artifactDetected === true
    ? `检出${severityLabel(severity)}金属伪影，建议结合原始图像复核。`
    : "未见明确金属伪影影响，但仍需结合原始影像确认。";
  const lesionText = reportSuggestion || (lesionStatus === "success"
    ? "病灶模型已返回结果，请结合置信度和原始影像复核。"
    : "病灶模型未返回可用于报告的明确结构化结果。");

  return `
    <div class="ai-readable">
      <div class="summary-grid">
        ${summaryCard("图像质量", severityLabel(severity), artifactText)}
        ${summaryCard("伪影比例", formatPercent(artifactRatio), `影响层面：${formatSliceList(affectedSlices)}`)}
        ${summaryCard("病灶识别", lesionStatus === "success" ? "已完成" : "需人工复核", lesionText)}
        ${summaryCard("AI链路", formatAiWorkflowLabel(modelVersions), "结果已进入医生复核流程")}
      </div>

      <section class="ai-section">
        <h3>AI 辅助结论</h3>
        <p>${escapeHtml(artifactText)}</p>
        <p>${escapeHtml(lesionText)}</p>
        ${confidenceMeter("病灶阳性置信度", positiveProbability)}
      </section>

      ${listBlock("建议医生重点复核", reviewFocus.length ? reviewFocus : [
        affectedSlices.length ? `复核第 ${formatSliceList(affectedSlices)} 层及邻近层面。` : "",
        "结合原始 CT 图像、病史和临床症状完成最终判断。"
      ])}
      ${listBlock("局限性与注意事项", limitations.length ? limitations : [
        "AI 结果仅供辅助参考，最终结论需医生审核。",
        "置信度代表模型输出强度，不等同于临床最终诊断概率。"
      ])}
      ${listBlock("系统提示", warnings)}
      ${renderPreviewImages(previewUrls)}
    </div>`;
}

function renderReferenceRows(rows) {
  if (!rows.length) return `<div class="empty-inline">暂无知识引用。</div>`;
  return rows.map((row) => {
    const title = row.title || row.source_id || "知识片段";
    const score = row.rerank_score ?? row.similarity ?? row.score;
    const tags = asArray(row.tags).join("、");
    const excerpt = row.content || row.snippet || row.summary || "";
    return `
      <article class="detail-card">
        <div class="detail-card-head">
          <strong>${escapeHtml(title)}</strong>
          ${score !== undefined && score !== null ? `<span>相关度 ${formatPercent(score)}</span>` : ""}
        </div>
        ${tags ? `<small>标签：${escapeHtml(tags)}</small>` : ""}
        ${excerpt ? `<p>${escapeHtml(String(excerpt).slice(0, 260))}</p>` : ""}
      </article>`;
  }).join("");
}

function renderVersionRows(rows) {
  if (!rows.length) return `<div class="empty-inline">暂无版本记录。</div>`;
  return rows.map((row) => `
    <article class="detail-card">
      <div class="detail-card-head">
        <strong>版本 ${escapeHtml(row.version_number || row.version || "-")}</strong>
        <span>${escapeHtml(formatTime(row.created_at || row.updated_at))}</span>
      </div>
      <p>${escapeHtml(String(row.change_reason || row.status || "报告版本已保存。"))}</p>
      ${row.findings ? `<small>影像所见摘要：${escapeHtml(String(row.findings).slice(0, 120))}</small>` : ""}
    </article>`).join("");
}

function renderAuditRows(rows) {
  if (!rows.length) return `<div class="empty-inline">暂无审计记录。</div>`;
  return rows.map((row) => `
    <article class="detail-card">
      <div class="detail-card-head">
        <strong>${escapeHtml(row.action || row.event_type || "操作记录")}</strong>
        <span>${escapeHtml(formatTime(row.created_at || row.event_time))}</span>
      </div>
      <p>操作人：${escapeHtml(row.actor_id || "-")}（${escapeHtml(row.actor_role || "未知角色")}）</p>
      ${row.comment || row.decision ? `<small>${escapeHtml(row.comment || row.decision)}</small>` : ""}
    </article>`).join("");
}

async function renderTab() {
  if (!state.current) return;
  document.querySelectorAll(".tab").forEach((node) => {
    const active = node.dataset.tab === state.activeTab;
    node.classList.toggle("active", active);
    node.setAttribute("aria-selected", String(active));
  });
  const panel = $("detailPanel");
  if (state.activeTab === "ai") {
    panel.innerHTML = renderAiInterpretation();
    return;
  }
  const endpoint = state.activeTab === "references" ? "references" : state.activeTab === "versions" ? "versions" : "audit-events";
  const payload = await api(`/api/v1/reports/${state.current.id}/${endpoint}`);
  const rows = payload.references || payload.versions || payload.events || [];
  if (state.activeTab === "references") panel.innerHTML = renderReferenceRows(rows);
  else if (state.activeTab === "versions") panel.innerHTML = renderVersionRows(rows);
  else panel.innerHTML = renderAuditRows(rows);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
}
function formatTime(value) { return value ? new Date(value).toLocaleString("zh-CN", { hour12: false }) : "-"; }

$("refreshButton").addEventListener("click", () => loadReports(false).catch((e) => toast(e.message, true)));
$("statusFilter").addEventListener("change", () => loadReports(false).catch((e) => toast(e.message, true)));
$("actorRole").addEventListener("change", () => state.current && renderReport());
$("saveButton").addEventListener("click", saveDraft);
$("submitButton").addEventListener("click", () => action("submit-review"));
$("approveButton").addEventListener("click", () => action("approve", "POST", { comment: "审核通过" }));
$("revisionButton").addEventListener("click", () => {
  const comment = window.prompt("请输入退回修订原因");
  if (comment) action("request-revision", "POST", { comment });
});
$("signButton").addEventListener("click", () => window.confirm("确认以当前医生身份签署此报告版本？") && action("sign"));
$("releaseButton").addEventListener("click", () => window.confirm("确认发布已签署报告？") && action("release"));
document.querySelectorAll(".tab").forEach((node) => node.addEventListener("click", () => { state.activeTab = node.dataset.tab; renderTab(); }));

applyEmbeddedIdentity();
loadHealth();
loadReports(false).catch((error) => toast(error.message, true));
