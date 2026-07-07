from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "frontend" / "src" / "router" / "index.ts"
REPORT = ROOT / "全项目界面与交互覆盖矩阵_2026-07-03.md"


@dataclass
class RouteItem:
    path: str
    name: str
    component: str
    role: str


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def extract_routes() -> list[RouteItem]:
    source = read(ROUTER)
    routes: list[RouteItem] = []
    current_parent = ""
    current_role = "PUBLIC"
    for line in source.splitlines():
        parent_match = re.search(r"path:\s*'(/[^']*)'", line)
        if parent_match and "component:" not in line and "redirect" not in line:
            path = parent_match.group(1)
            if path in {"/patient", "/doctor", "/admin", "/mini-patient", "/medical-tech", "/drugstore"}:
                current_parent = path
                current_role = {
                    "/patient": "PATIENT",
                    "/doctor": "DOCTOR",
                    "/admin": "ADMIN",
                    "/mini-patient": "PATIENT_MINI",
                    "/medical-tech": "MEDICAL_TECH",
                    "/drugstore": "PHARMACIST",
                }[path]
        child_match = re.search(
            r"\{\s*path:\s*'([^']*)'.*?name:\s*'([^']*)'.*?component:\s*\(\)\s*=>\s*import\('@\/views\/([^']+)'\)",
            line,
        )
        if child_match:
            child_path, name, component = child_match.groups()
            if child_path.startswith("/"):
                full_path = child_path
                role = "PUBLIC"
            elif current_parent:
                full_path = f"{current_parent}/{child_path}".replace("//", "/").rstrip("/")
                role = current_role
            else:
                full_path = child_path
                role = "PUBLIC"
            routes.append(RouteItem(full_path or current_parent, name, f"frontend/src/views/{component}", role))
    return routes


def extract_interactions(path: Path) -> list[str]:
    text = read(path)
    patterns = [
        r"@click(?:\.[\w.]+)?=\"([^\"]+)\"",
        r"@submit(?:\.[\w.]+)?=\"([^\"]+)\"",
        r"@change(?:\.[\w.]+)?=\"([^\"]+)\"",
        r"@confirm=\"([^\"]+)\"",
        r"@cancel=\"([^\"]+)\"",
        r"addEventListener\(\"([^\"]+)\",\s*([^)]+)\)",
        r"<(?:van-button|el-button|button|input|select|textarea)\b([^>]*)>",
    ]
    interactions: list[str] = []
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            value = " ".join(part.strip() for part in match.groups() if part)
            value = re.sub(r"\s+", " ", value)
            if value and value not in interactions:
                interactions.append(value)
    return interactions


def main() -> None:
    routes = extract_routes()
    standalone = [
        ("REPORT_WORKSPACE", "http://127.0.0.1:8030", ROOT / "HeadCTReportService" / "frontend" / "index.html"),
        ("FILTER_WORKSPACE", "http://127.0.0.1:8000", ROOT / "Filter" / "Fastapi" / "frontend" / "index.html"),
    ]
    lines = [
        "# 全项目界面与交互覆盖矩阵",
        "",
        "本矩阵由脚本扫描生成，用于约束截图级验收范围。所有路由页面、独立前端页面和可扫描交互点均必须在最终截图验收中有对应证据或明确说明不可自动触发原因。",
        "",
        "## Vue 主前端路由",
        "",
        "| # | 角色 | 路由 | 组件 | 交互点数量 | 交互摘要 |",
        "|---|---|---|---|---:|---|",
    ]
    for idx, route in enumerate(routes, 1):
        component_path = ROOT / route.component
        interactions = extract_interactions(component_path) if component_path.exists() else []
        summary = "<br>".join(f"`{item[:100]}`" for item in interactions[:12])
        if len(interactions) > 12:
            summary += f"<br>... 另 {len(interactions) - 12} 项"
        lines.append(f"| {idx} | {route.role} | `{route.path}` | `{route.component}` | {len(interactions)} | {summary or '无显式交互'} |")

    lines.extend(["", "## 独立前端入口", "", "| # | 模块 | 地址 | 文件 | 交互点数量 | 交互摘要 |", "|---|---|---|---|---:|---|"])
    for idx, (name, url, path) in enumerate(standalone, 1):
        js_path = path.with_name("app.js")
        interactions = extract_interactions(path)
        if js_path.exists():
            interactions += [item for item in extract_interactions(js_path) if item not in interactions]
        summary = "<br>".join(f"`{item[:100]}`" for item in interactions[:14])
        if len(interactions) > 14:
            summary += f"<br>... 另 {len(interactions) - 14} 项"
        lines.append(f"| {idx} | {name} | `{url}` | `{path.relative_to(ROOT).as_posix()}` | {len(interactions)} | {summary or '无显式交互'} |")

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"routes={len(routes)}")
    print(f"report={REPORT}")


if __name__ == "__main__":
    main()
