from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"
ROUNDS = 20
REPORT = ROOT / "目前存在问题_20轮用户点击验收记录_2026-07-03.md"
SCREENSHOT_INDEX = ROOT / "目前存在问题_20轮用户点击截图索引_2026-07-03.md"
SCREENSHOT_ROOT = ROOT / "frontend" / "visual-results" / "current-issues-click-acceptance"


def run_command(args: list[str], cwd: Path, timeout: int, round_no: int) -> tuple[int, str]:
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["CURRENT_ISSUE_ACCEPTANCE_ROUND"] = str(round_no)
    env.setdefault("PLAYWRIGHT_ARTIFACT_ROOT", str(ROOT / ".tmp" / "playwright-current-issues-20-rounds"))
    proc = subprocess.run(
        args,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        env=env,
    )
    return proc.returncode, proc.stdout


def append_report(rows: list[dict[str, object]]) -> None:
    lines = [
        "# 目前存在问题 20 轮用户点击验收记录",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "每轮均通过真实浏览器鼠标点击执行，不使用前端 token 注入，不直接进入业务页面。",
        "",
        "| 轮次 | 结果 | 耗时/证据 | 截图目录 |",
        "|---|---|---|---|",
    ]
    for row in rows:
        evidence = str(row.get("evidence", "")).replace("|", "/").replace("\n", " ")
        screenshot_dir = f"frontend/visual-results/current-issues-click-acceptance/round-{int(row['round']):02d}/"
        lines.append(f"| {row['round']} | {row['status']} | {evidence} | {screenshot_dir} |")
    passed = sum(1 for row in rows if row["status"] == "PASS")
    lines.extend(
        [
            "",
            "## 结论",
            "",
            f"通过轮数：{passed}/{ROUNDS}",
            "",
            "逐轮截图证据：`frontend/visual-results/current-issues-click-acceptance/round-01/` 至 `round-20/`",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_screenshot_index(rows: list[dict[str, object]]) -> None:
    lines = [
        "# 目前存在问题 20 轮用户点击截图索引",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        "以下截图均由 Playwright 真实浏览器鼠标点击流程生成。每轮包含员工登录、管理员 AI 排班、历史查询、返回首页、退出、患者登录、联系客服、挂号、空表单反馈、确认挂号、记录页、首页和我的页等关键交互。",
        "",
    ]
    for row in rows:
        round_no = int(row["round"])
        round_dir = SCREENSHOT_ROOT / f"round-{round_no:02d}"
        lines.append(f"## Round {round_no:02d} - {row['status']}")
        lines.append("")
        if not round_dir.exists():
            lines.append(f"截图目录不存在：`{round_dir.relative_to(ROOT).as_posix()}`")
            lines.append("")
            continue
        for image in sorted(round_dir.glob("*.png")):
            rel = image.relative_to(ROOT).as_posix()
            lines.append(f"![{image.stem}]({rel})")
            lines.append("")
    SCREENSHOT_INDEX.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows: list[dict[str, object]] = []
    command = [
        "npx.cmd" if os.name == "nt" else "npx",
        "playwright",
        "test",
        "-c",
        "playwright.config.ts",
        "tests/visual/current-issues-click-acceptance.spec.ts",
        "--project=desktop-chrome",
    ]

    for round_no in range(1, ROUNDS + 1):
        started = datetime.now()
        code, output = run_command(command, FRONTEND, timeout=120, round_no=round_no)
        elapsed = (datetime.now() - started).total_seconds()
        ok = code == 0 and "1 passed" in output
        rows.append(
            {
                "round": round_no,
                "status": "PASS" if ok else "FAIL",
                "elapsed_seconds": round(elapsed, 1),
                "evidence": f"{round(elapsed, 1)}s; {'1 passed' if ok else output[-700:]}",
            }
        )
        append_report(rows)
        write_screenshot_index(rows)
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
        if not ok:
            return code or 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
