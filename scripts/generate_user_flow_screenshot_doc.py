from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "user_flow_screenshot_acceptance_2026-07-06.md"

SECTIONS = [
    ("A. 当前全项目页面截图", Path("frontend/visual-results")),
    ("B. 头部 CT 真实用户链路", Path("frontend/visual-results/headct-real-user-workflow")),
    ("C. 填写态、禁用态与筛选态专项补强", Path("frontend/visual-results/fill-and-disabled-coverage")),
    ("D. 医生接诊五部分填写与交互", Path("frontend/visual-results/doctor-visit-five-tabs")),
]

NAME_MAP = {
    "admin": "管理员",
    "patient": "患者",
    "doctor": "医生",
    "login": "登录",
    "home": "首页",
    "schedule": "排班",
    "history": "历史",
    "query": "查询",
    "generated": "生成结果",
    "register": "挂号",
    "success": "成功反馈",
    "form": "表单",
    "filled": "已填写",
    "empty": "空表单",
    "feedback": "反馈",
    "drugstore": "药房",
    "inventory": "库存",
    "toast": "浮层反馈",
    "headct": "头部 CT",
    "report": "报告",
    "workflow": "流程",
    "ai": "AI",
    "recognition": "识别",
    "visual": "可视化",
    "output": "输出",
    "records": "记录",
    "profile": "我的/资料",
    "customer": "客服",
    "service": "服务",
    "return": "返回",
    "tabbar": "底部导航",
    "logout": "退出",
    "appointment": "预约",
    "selected": "已选择",
    "dept": "科室",
    "page": "页面",
    "entry": "入口",
    "disabled": "禁用态",
    "enabled": "可提交态",
    "filter": "筛选",
    "medicaltech": "医技",
    "lab": "检验",
    "record": "病历",
    "check": "检查检验",
    "result": "结果",
    "confirm": "确诊",
    "prescription": "处方",
    "tab": "分区",
    "blocked": "已阻止",
    "items": "项目",
}


def rel(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def human(filename: str) -> str:
    text = " ".join(Path(filename).stem.split("-"))
    for source, target in NAME_MAP.items():
        text = text.replace(source, target)
    return text


def main() -> None:
    lines: list[str] = [
        "# 用户流程截图级验收流程图 2026-07-06",
        "",
        "本文件用于补齐“截图必须插入文档并附文字说明”的硬门禁。以下截图均来自本地 `frontend/visual-results` 下已生成的 Playwright 真实浏览器验收结果。",
        "",
        "## 总体用户行为流程图",
        "",
        "```mermaid",
        "flowchart TD",
        "  A[员工登录] --> B[管理员首页]",
        "  B --> C[AI排班]",
        "  C --> D[查询历史排班]",
        "  C --> E[生成排班并注册号源]",
        "  B --> F[收费退费/药房库存]",
        "  G[患者登录] --> H[患者首页]",
        "  H --> I[联系客服]",
        "  H --> J[预约挂号]",
        "  J --> K[选择科室/医生]",
        "  K --> L[填写并确认挂号]",
        "  L --> M[病历/首页/我的联动]",
        "  N[医生登录] --> O[接诊工作台]",
        "  O --> P[上传头部 CT 并 AI 识别]",
        "  P --> Q[报告工作台审核发布]",
        "  Q --> R[EMR 归档]",
        "```",
        "",
    ]

    summary = []
    for title, directory in SECTIONS:
        base = ROOT / directory
        if title.startswith("A."):
            files = sorted(base.glob("*.png")) if base.exists() else []
        else:
            files = sorted(base.rglob("*.png")) if base.exists() else []
        summary.append((title, directory, files))

    lines.extend(["## 截图覆盖统计", "", "| 范围 | 截图目录 | 嵌入截图数 |", "|---|---|---:|"])
    for title, directory, files in summary:
        lines.append(f"| {title} | `{directory.as_posix()}` | {len(files)} |")
    lines.extend(
        [
            "",
            "> 注意：嵌入截图数表示本文件实际插入的 Markdown 图片数量。若某个自动验收动作在原报告中标记为 SKIP，本文件只能嵌入已有截图，不能把 SKIP 伪装为已覆盖。",
        ]
    )

    for title, directory, files in summary:
        lines.extend(["", f"## {title}", ""])
        if not files:
            lines.append("未覆盖：未找到截图文件。")
            continue
        current_group = None
        for index, screenshot in enumerate(files, 1):
            group = screenshot.parent.relative_to(ROOT / directory).as_posix() if screenshot.parent != ROOT / directory else "root"
            if group != current_group:
                current_group = group
                lines.extend(["", f"### {group}", ""])
            caption = human(screenshot.name)
            lines.extend(
                [
                    f"#### {index}. {caption}",
                    "",
                    f"- 用户动作/系统反馈：{caption}。",
                    f"- 截图文件：`{rel(screenshot)}`",
                    "",
                    f"![{caption}]({rel(screenshot)})",
                    "",
                ]
            )

    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote={OUT}")
    print(f"embedded_images={sum(len(files) for _, _, files in summary)}")
    print(f"bytes={OUT.stat().st_size}")


if __name__ == "__main__":
    main()
