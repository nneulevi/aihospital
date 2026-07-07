"""Check that current Project2 controllers cover remote aihospital/master APIs.

The acceptance standard requires checking remote master coverage before final
acceptance. This script compares business URL paths from remote Project2
controllers against the current working tree. It intentionally checks URL
coverage, not one-to-one file names, because some remote controllers were
merged into broader current controllers.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTROLLER_DIR = ROOT / "Project2" / "src" / "main" / "java" / "com" / "neuedu" / "his" / "controller"
REMOTE_REF = "aihospital/master"
REMOTE_CONTROLLER_PREFIX = "Project2/src/main/java/com/neuedu/his/controller"

MAPPING_RE = re.compile(r"@(Request|Get|Post|Put|Delete|Patch)Mapping\s*\(\s*(?:value\s*=\s*)?\"([^\"]*)\"")


def run_git(args: list[str]) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        text=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def join_path(base: str, child: str) -> str:
    if not base:
        return child or "/"
    if not child:
        return base
    return f"{base.rstrip('/')}/{child.lstrip('/')}"


def extract_endpoints(source: str) -> set[str]:
    base = ""
    endpoints: set[str] = set()
    for kind, path in MAPPING_RE.findall(source):
        if kind == "Request" and not base:
            base = path
            continue
        if kind != "Request":
            endpoints.add(join_path(base, path))
    return endpoints


def remote_controller_sources() -> dict[str, str]:
    files = run_git(["ls-tree", "-r", "--name-only", REMOTE_REF, REMOTE_CONTROLLER_PREFIX]).splitlines()
    return {path: run_git(["show", f"{REMOTE_REF}:{path}"]) for path in files if path.endswith(".java")}


def current_controller_sources() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)).replace("\\", "/"): path.read_text(encoding="utf-8", errors="ignore")
        for path in CONTROLLER_DIR.glob("*.java")
    }


def main() -> None:
    remote_endpoints = set()
    for source in remote_controller_sources().values():
        remote_endpoints.update(extract_endpoints(source))

    current_endpoints = set()
    for source in current_controller_sources().values():
        current_endpoints.update(extract_endpoints(source))

    missing = sorted(remote_endpoints - current_endpoints)
    if missing:
        raise SystemExit("Remote master business API coverage check failed:\n- " + "\n- ".join(missing))

    print(f"Remote master business API coverage passed: {len(remote_endpoints)} remote endpoints covered.")


if __name__ == "__main__":
    main()
