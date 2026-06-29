const state = { reports: [], current: null, activeTab: "ai" };
const $ = (id) => document.getElementById(id);
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
  $("studyMeta").textContent = `${r.department || "未分配科室"} · 检查 ${r.study_id} · 版本 ${r.version_number}`;
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

async function renderTab() {
  if (!state.current) return;
  document.querySelectorAll(".tab").forEach((node) => node.classList.toggle("active", node.dataset.tab === state.activeTab));
  const panel = $("detailPanel");
  if (state.activeTab === "ai") {
    panel.innerHTML = `<pre>${escapeHtml(JSON.stringify({
      quality_control: state.current.quality_control_json,
      lesion_analysis: state.current.lesion_analysis_json,
      model_versions: state.current.model_versions
    }, null, 2))}</pre>`;
    return;
  }
  const endpoint = state.activeTab === "references" ? "references" : state.activeTab === "versions" ? "versions" : "audit-events";
  const payload = await api(`/api/v1/reports/${state.current.id}/${endpoint}`);
  const rows = payload.references || payload.versions || payload.events || [];
  panel.innerHTML = rows.length ? rows.map((row) => `<div class="detail-row"><pre>${escapeHtml(JSON.stringify(row, null, 2))}</pre></div>`).join("") : "暂无记录";
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

loadHealth();
loadReports(false).catch((error) => toast(error.message, true));
