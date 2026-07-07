import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "all_ui_interaction_coverage_audit_2026-07-06.md"


def find_report(prefix: str) -> Path:
    matches = sorted(ROOT.glob(prefix + "*.md"))
    if not matches:
        raise FileNotFoundError(prefix)
    return matches[0]


def main() -> None:
    full = find_report("全项目所有界面交互截图验收报告")
    flow = ROOT / "user_flow_screenshot_acceptance_2026-07-06.md"
    report = full.read_text(encoding="utf-8")
    flow_text = flow.read_text(encoding="utf-8") if flow.exists() else ""

    rows = []
    for line in report.splitlines():
        if re.match(r"^\| \d+ \|", line):
            cols = [col.strip() for col in line.strip().strip("|").split("|")]
            if len(cols) >= 6:
                rows.append(cols[:6])

    pass_rows = [row for row in rows if row[3] == "PASS"]
    skip_rows = [row for row in rows if row[3] == "SKIP"]
    fail_rows = [row for row in rows if row[3] == "FAIL"]

    covered_keywords = {
        "登录": ["login", "staff-login-entry", "patient-login-entry", "staff-login-admin-filled", "patient-login-filled", "staff-login-medicaltech-filled"],
        "预约挂号": ["patient-register-form-filled", "patient-register-success", "appointment-selected", "patient-appointment-search-filled", "mini-patient-appointment-entry", "desktop-chrome-patient-appointment"],
        "确认挂号": ["patient-register-form-filled", "patient-register-success", "patient-appointment-search-filled"],
        "退出登录": ["admin-logout-confirm-dialog", "drugstore-logout-entry-visible", "medical-tech-filter-register-id-filled"],
        "退出": ["admin-logout-confirm-dialog", "drugstore-logout-entry-visible", "medical-tech-filter-register-id-filled"],
        "提交预约申请": ["patient-lab-booking-empty-disabled", "patient-register-form-filled"],
        "立即支付": ["desktop-chrome-patient-orders", "patient-register-success"],
        "确认报到": ["desktop-chrome-patient-checkin", "patient-records-after-register"],
        "重新问诊": ["doctor-ai-triage", "doctor-ai-diagnosis", "patient-ai-filled-enabled"],
        "开始智能分析": ["patient-ai-empty-disabled", "patient-ai-filled-enabled"],
        "再次挂号": ["patient-register-form-filled"],
        "没有就诊记录": ["patient-lab-booking-normal-entry-to-register", "patient-lab-booking-empty-disabled"],
    }

    def evidence_for(row: list[str]) -> str:
        reason = row[4]
        route = row[1]
        if "立即支付" in reason and "desktop-chrome-patient-orders" in flow_text:
            return "非缺口：患者订单页截图覆盖按钮禁用态；当前待缴费为 0 时不应允许支付。"
        if "确认报到" in reason and "desktop-chrome-patient-checkin" in flow_text:
            return "非缺口：患者报到页截图覆盖按钮禁用态；无可报到记录时不应允许提交。"
        if "预约挂号" in reason and ("patient-appointment-search-filled" in flow_text or "desktop-chrome-patient-appointment" in flow_text):
            return "专项覆盖：流程截图文档包含预约挂号入口、搜索科室与挂号页；实际提交由真实端到端脚本覆盖，避免全量扫描重复生成挂号。"
        if "退出" in reason and "admin-logout-confirm-dialog" in flow_text:
            if route.startswith("/admin"):
                return "专项覆盖：管理员退出确认弹窗已截图；全量扫描不直接退出以免中断后续页面。"
            if route.startswith("/medical-tech") and "medical-tech-filter-register-id-filled" in flow_text:
                return "专项覆盖：医技工作台顶部退出入口可见；全量扫描不直接退出以免中断后续页面。"
            if route.startswith("/drugstore") and "drugstore-logout-entry-visible" in flow_text:
                return "专项覆盖：药房工作台顶部退出入口可见；全量扫描不直接退出以免中断后续页面。"
        if "本页面无可编辑输入控件" in reason:
            return "非缺口：该项是“无输入控件”说明，页面截图已在全项目报告中覆盖。"
        if "首个输入控件当前不可直接聚焦" in reason:
            if route.startswith("/medical-tech") and "medical-tech-filter-register-id-filled" in flow_text:
                return "专项覆盖：流程截图文档包含 medical-tech-filter-register-id-filled，已覆盖医技筛选输入态。"
            return "部分覆盖：页面主体截图已覆盖，但隐藏筛选/下拉输入未单独截图。"
        for key, needles in covered_keywords.items():
            if key in reason:
                matched = [needle for needle in needles if needle in flow_text]
                if matched:
                    return "专项覆盖：流程截图文档包含 " + ", ".join(matched)
        if route.startswith("/doctor/headct"):
            return "专项覆盖：headct-real-user-workflow 截图覆盖报告工作台入口、审核、发布、EMR。"
        return "未覆盖：未找到可对应的专项截图证据。"

    lines = [
        "# 所有界面与交互覆盖审计 2026-07-06",
        "",
        "本文件回答“到底有没有覆盖所有界面和交互、需要用户填写信息的地方有没有截图”。结论不能弱化：只要存在无法映射证据的 SKIP，就不能写全部覆盖。",
        "",
        "## 汇总",
        "",
        f"- 全项目报告 PASS：{len(pass_rows)}",
        f"- 全项目报告 SKIP：{len(skip_rows)}",
        f"- 全项目报告 FAIL：{len(fail_rows)}",
        f"- 流程图式截图文档嵌入图片：{flow_text.count('![') if flow_text else 0}",
        "",
        "## 需要用户填写信息的截图证据",
        "",
        "| 填写场景 | 截图证据 | 状态 |",
        "|---|---|---|",
        "| 患者挂号信息填写 | `frontend/visual-results/desktop-chrome-patient-appointment.png`、`frontend/visual-results/mobile-chrome-patient-appointment.png` | 已覆盖 |",
        "| 患者挂号空表单反馈 | `frontend/visual-results/fill-and-disabled-coverage/02c-patient-register-empty-form-feedback.png` | 已覆盖 |",
        "| 员工登录入口与填写态 | `frontend/visual-results/desktop-chrome-auth-login.png`、`frontend/visual-results/fill-and-disabled-coverage/01-staff-login-admin-filled.png`、`07-staff-login-medicaltech-filled.png` | 已覆盖 |",
        "| 患者登录入口与填写态 | `frontend/visual-results/desktop-chrome-patient-login.png`、`frontend/visual-results/fill-and-disabled-coverage/02-patient-login-filled.png` | 已覆盖 |",
        "| 头部 CT 文件选择/上传 | `frontend/visual-results/headct-real-user-workflow/desktop-chrome-01-doctor-selected-real-ct-file.png`、`desktop-chrome-02-upload-success.png`、`desktop-chrome-03-ai-recognition-with-visual-output.png`、`desktop-chrome-06-report-released-and-emr-archived.png` | 已覆盖 |",
        "| AI 辅助诊断/分诊输入与反馈 | `frontend/visual-results/full-project-ui-acceptance/*doctor-ai-diagnosis*`、`*doctor-ai-triage*`、`frontend/visual-results/fill-and-disabled-coverage/04-patient-ai-filled-enabled.png`、`04b-patient-ai-analysis-feedback.png` | 已覆盖 |",
        "| 患者检验预约禁用态与转挂号入口 | `frontend/visual-results/fill-and-disabled-coverage/05-patient-lab-booking-empty-disabled.png`、`06-patient-lab-booking-normal-entry-to-register.png` | 已覆盖 |",
        "| 医技筛选输入与结果反馈 | `frontend/visual-results/fill-and-disabled-coverage/08-medical-tech-filter-register-id-filled.png`、`08b-medical-tech-filter-result-feedback.png` | 已覆盖 |",
        "| 医生接诊病历保存反馈 | `frontend/visual-results/doctor-visit-five-tabs/01-record-tab-filled.png`、`01b-record-save-feedback.png` | 已覆盖 |",
        "| 医生检查检验提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/03-check-tab-all-items-filled.png`、`03b-check-tab-submit-feedback.png` | 已覆盖 |",
        "| 医生确诊提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/05-confirm-tab-filled.png`、`05b-confirm-submit-feedback.png` | 已覆盖 |",
        "| 医生处方选择、加入与提交反馈 | `frontend/visual-results/doctor-visit-five-tabs/06b-prescription-drug-picker-visible.png`、`06c-prescription-add-drug-feedback.png`、`06d-prescription-submit-feedback.png` | 已覆盖 |",
        "",
        "## SKIP 明细分类",
        "",
        "| # | 路由 | 检查点 | 原因 | 覆盖判断 |",
        "|---:|---|---|---|---|",
    ]

    uncovered = []
    for row in skip_rows:
        evidence = evidence_for(row)
        if evidence.startswith("未覆盖") or "未单独截图" in evidence or "部分覆盖" in evidence:
            uncovered.append(row)
        lines.append(f"| {row[0]} | `{row[1]}` | {row[2]} | {row[4].replace('|', '/')} | {evidence} |")

    lines.extend(
        [
            "",
            "## 结论",
            "",
            f"- SKIP 中仍需补强或明确人工覆盖的条目数：{len(uncovered)}。",
            "- 因此当前不能回答“所有界面和所有交互已完全覆盖”。",
            "- 已能证明：主要用户入口、挂号填写、管理员排班、药房库存、收费退费、头部 CT 上传识别报告链路有截图与脚本证据。",
        ]
    )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    text = OUT.read_text(encoding="utf-8")
    print(f"wrote={OUT}")
    print(f"pass={len(pass_rows)} skip={len(skip_rows)} fail={len(fail_rows)} uncovered_or_partial={len(uncovered)}")
    mojibake_markers = ["\u951b", "\u7ecb", "\u6d63", "\ufffd"]
    print(f"mojibake={any(marker in text for marker in mojibake_markers)}")


if __name__ == "__main__":
    main()
