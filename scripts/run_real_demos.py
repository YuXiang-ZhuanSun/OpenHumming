import json
import os
import socket
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

import httpx


@dataclass(slots=True)
class DemoResult:
    demo_id: str
    passed: bool
    details: list[str]
    response_preview: str = ""


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "examples" / "real_demos"
SHOWCASE_DIR = DEMO_DIR / "showcase"
WORKSPACE_ROOT = DEMO_DIR / "workspace"
REPORT_PATH = DEMO_DIR / "last_run_report.md"
SERVER_LOG_PATH = DEMO_DIR / "last_server.log"
SUITE_PATH = DEMO_DIR / "demo_suite.json"
DEMO_PROVIDER_ENV = "OPENHUMMING_DEMO_PROVIDER"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    _reset_workspace()
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"
    server = _start_server(port)
    try:
        _wait_for_server(server, base_url)
        results = [_run_demo(item, base_url) for item in suite]
    finally:
        _stop_server(server)

    _write_report(results)
    _write_showcase_snapshots()
    failed = [result for result in results if not result.passed]
    return 1 if failed else 0


def _reset_workspace() -> None:
    if WORKSPACE_ROOT.exists():
        shutil.rmtree(WORKSPACE_ROOT)
    if SERVER_LOG_PATH.exists():
        SERVER_LOG_PATH.unlink()


def _start_server(port: int) -> subprocess.Popen[str]:
    env = _build_demo_server_env(port)
    log_handle = SERVER_LOG_PATH.open("w", encoding="utf-8")
    return subprocess.Popen(
        [sys.executable, "scripts/dev_server.py"],
        cwd=REPO_ROOT,
        env=env,
        stdout=log_handle,
        stderr=log_handle,
        text=True,
    )


def _wait_for_server(
    server: subprocess.Popen[str],
    base_url: str,
    timeout_seconds: int = 60,
) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if server.poll() is not None:
            log_output = SERVER_LOG_PATH.read_text(encoding="utf-8") if SERVER_LOG_PATH.exists() else ""
            raise RuntimeError(f"Demo server exited early.\n{log_output}")
        try:
            response = httpx.get(f"{base_url}/health", timeout=2.0)
            if response.status_code == 200:
                return
        except httpx.HTTPError:
            time.sleep(0.5)
            continue
        time.sleep(0.5)
    log_output = SERVER_LOG_PATH.read_text(encoding="utf-8") if SERVER_LOG_PATH.exists() else ""
    raise RuntimeError(f"Demo server did not become healthy in time.\n{log_output}")


def _stop_server(server: subprocess.Popen[str]) -> None:
    if server.poll() is None:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()


def _run_demo(item: dict[str, Any], base_url: str) -> DemoResult:
    demo_type = item["type"]
    if demo_type == "chat":
        response = httpx.post(
            f"{base_url}/chat",
            json={
                "message": item["message"],
                "session_id": item["session_id"],
            },
            timeout=120.0,
        )
        payload = _decode_response_payload(response)
        if not isinstance(payload, dict):
            return DemoResult(
                demo_id=item["id"],
                passed=False,
                details=[
                    f"Expected JSON object response from /chat, got {type(payload).__name__}.",
                    f"HTTP status was {response.status_code}.",
                ],
                response_preview=_preview(str(payload)),
            )
        return _evaluate_chat_demo(item, response.status_code, payload)
    if demo_type == "daily_review":
        response = httpx.post(f"{base_url}/reviews/daily", timeout=120.0)
        payload = _decode_response_payload(response)
        if not isinstance(payload, dict):
            return DemoResult(
                demo_id=item["id"],
                passed=False,
                details=[
                    f"Expected JSON object response from /reviews/daily, got {type(payload).__name__}.",
                    f"HTTP status was {response.status_code}.",
                ],
                response_preview=_preview(str(payload)),
            )
        return _evaluate_daily_review_demo(item, response.status_code, payload)
    return DemoResult(
        demo_id=item["id"],
        passed=False,
        details=[f"Unsupported demo type: {demo_type}"],
    )


def _evaluate_chat_demo(
    item: dict[str, Any],
    status_code: int,
    payload: dict[str, Any],
) -> DemoResult:
    details: list[str] = []
    passed = status_code == 200
    if status_code != 200:
        details.append(f"HTTP status was {status_code}.")
        return DemoResult(item["id"], False, details, str(payload))

    actions = payload.get("actions", [])
    for action in item.get("expect_actions", []):
        if action not in actions:
            passed = False
            details.append(f"Missing expected action: {action}")

    expected_memory_updates = item.get("expect_memory_updates", {})
    actual_memory_updates = payload.get("memory_updates", {})
    for key, expected_value in expected_memory_updates.items():
        if actual_memory_updates.get(key) != expected_value:
            passed = False
            details.append(
                f"Memory update mismatch for {key}: expected {expected_value}, got {actual_memory_updates.get(key)}"
            )

    file_expectation = item.get("expect_file")
    if file_expectation:
        target = WORKSPACE_ROOT / file_expectation["path"]
        if not target.exists():
            passed = False
            details.append(f"Expected file was not created: {target}")
        else:
            content = target.read_text(encoding="utf-8")
            if file_expectation["contains"] not in content:
                passed = False
                details.append(f"Expected file content not found in {target}")

    draft_expectation = item.get("expect_skill_draft")
    if draft_expectation:
        target = WORKSPACE_ROOT / draft_expectation["path"]
        if not target.exists():
            passed = False
            details.append(f"Expected skill draft was not created: {target}")
        else:
            content = target.read_text(encoding="utf-8")
            if draft_expectation["contains"] not in content:
                passed = False
                details.append(f"Expected draft metadata not found in {target}")

    expected_tasks = item.get("expect_tasks_count_at_least")
    if expected_tasks is not None:
        tasks_file = WORKSPACE_ROOT / "tasks" / "tasks.json"
        tasks = json.loads(tasks_file.read_text(encoding="utf-8"))
        if len(tasks) < expected_tasks:
            passed = False
            details.append(f"Expected at least {expected_tasks} task(s), found {len(tasks)}")

    for needle in item.get("expect_user_profile_contains", []):
        content = (WORKSPACE_ROOT / "user.md").read_text(encoding="utf-8")
        if needle not in content:
            passed = False
            details.append(f"Missing expected user profile text: {needle}")

    for needle in item.get("expect_agent_profile_contains", []):
        content = (WORKSPACE_ROOT / "agent.md").read_text(encoding="utf-8")
        if needle not in content:
            passed = False
            details.append(f"Missing expected agent profile text: {needle}")

    if not details:
        details.append("All checks passed.")
    return DemoResult(
        demo_id=item["id"],
        passed=passed,
        details=details,
        response_preview=_preview(payload.get("response", "")),
    )


def _evaluate_daily_review_demo(
    item: dict[str, Any],
    status_code: int,
    payload: dict[str, Any],
) -> DemoResult:
    details: list[str] = []
    passed = status_code == 200
    if status_code != 200:
        details.append(f"HTTP status was {status_code}.")
        return DemoResult(item["id"], False, details, str(payload))

    if item.get("expect_summary_created"):
        summary_path = WORKSPACE_ROOT / "summaries" / f"{date.today().isoformat()}.md"
        if not summary_path.exists():
            passed = False
            details.append(f"Expected summary file was not created: {summary_path}")

    if not details:
        details.append("All checks passed.")
    return DemoResult(
        demo_id=item["id"],
        passed=passed,
        details=details,
        response_preview=_preview(json.dumps(payload, ensure_ascii=False)),
    )


def _write_report(results: list[DemoResult]) -> None:
    passed_count = len([result for result in results if result.passed])
    failed_count = len(results) - passed_count
    lines = [
        "# Real Demo Report / 真实 Demo 报告",
        "",
        f"- Date / 日期: {date.today().isoformat()}",
        f"- Workspace / 工作区: `{WORKSPACE_ROOT}`",
        f"- Scenarios / 场景数量: {len(results)}",
        f"- Passed / 通过: {passed_count}",
        f"- Failed / 失败: {failed_count}",
        "",
    ]
    for result in results:
        status = "PASS / 通过" if result.passed else "FAIL / 失败"
        lines.extend(
            [
                f"## {result.demo_id} [{status}]",
                "",
                f"- Response preview / 响应预览: {result.response_preview or '(none)'}",
            ]
        )
        lines.extend(f"- {detail}" for detail in result.details)
        lines.append("")

    REPORT_PATH.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_showcase_snapshots() -> None:
    default_agent_profile, default_user_profile = _load_default_profiles()
    SHOWCASE_DIR.mkdir(parents=True, exist_ok=True)
    (SHOWCASE_DIR / "agent.before.md").write_text(
        default_agent_profile.strip() + "\n",
        encoding="utf-8",
    )
    (SHOWCASE_DIR / "user.before.md").write_text(
        default_user_profile.strip() + "\n",
        encoding="utf-8",
    )
    (SHOWCASE_DIR / "agent.after.md").write_text(
        (WORKSPACE_ROOT / "agent.md").read_text(encoding="utf-8").strip() + "\n",
        encoding="utf-8",
    )
    (SHOWCASE_DIR / "user.after.md").write_text(
        (WORKSPACE_ROOT / "user.md").read_text(encoding="utf-8").strip() + "\n",
        encoding="utf-8",
    )
    (SHOWCASE_DIR / "skills.before.md").write_text(
        _build_before_skills_snapshot(),
        encoding="utf-8",
    )
    (SHOWCASE_DIR / "skills.after.md").write_text(
        _build_after_skills_snapshot(),
        encoding="utf-8",
    )


def _build_before_skills_snapshot() -> str:
    return (
        "skills/\n"
        "|- example_skill.md\n"
        "`- drafts/\n"
        "   `- README.md\n\n"
        "# Skill: Create Agent Project Plan\n"
        "\n"
        "## Description\n"
        "\n"
        "Create a mature project plan for a Python-based agent runtime.\n"
    )


def _build_after_skills_snapshot() -> str:
    published_paths = sorted(
        path
        for path in (WORKSPACE_ROOT / "skills").glob("*.md")
        if path.name.lower() != "readme.md"
    )
    published = [path.name for path in published_paths]
    drafts = sorted(
        path.name
        for path in (WORKSPACE_ROOT / "skills" / "drafts").glob("*.md")
        if path.name.lower() != "readme.md"
    )
    lines = ["skills/"]
    for index, name in enumerate(published):
        branch = "|-" if index < len(published) else "`-"
        lines.append(f"{branch} {name}")
    lines.append("`- drafts/")
    if drafts:
        for index, name in enumerate(drafts):
            branch = "   |-" if index < len(drafts) - 1 else "   `-"
            lines.append(f"{branch} {name}")
    else:
        lines.append("   `- README.md")

    spotlight = _select_showcase_skill(published_paths)
    if spotlight is None:
        spotlight = next(
            (
                path
                for path in (WORKSPACE_ROOT / "skills" / "drafts").glob("*.md")
                if path.name.lower() != "readme.md"
            ),
            None,
        )

    if spotlight is not None:
        lines.extend(["", spotlight.read_text(encoding="utf-8").strip()])

    return "\n".join(lines).rstrip() + "\n"


def _select_showcase_skill(paths: list[Path]) -> Path | None:
    candidates = [
        path for path in paths if path.name.lower() not in {"readme.md", "example_skill.md"}
    ]
    if not candidates:
        return None
    return max(candidates, key=_spotlight_score)


def _spotlight_score(path: Path) -> tuple[float, float, str]:
    content = path.read_text(encoding="utf-8")
    times_reused = _extract_frontmatter_number(content, "times_reused")
    confidence = _extract_frontmatter_number(content, "confidence")
    return (times_reused, confidence, path.name.lower())


def _extract_frontmatter_number(content: str, key: str) -> float:
    prefix = f"{key}: "
    for line in content.splitlines():
        if not line.startswith(prefix):
            continue
        raw_value = line[len(prefix) :].strip().strip('"')
        try:
            return float(raw_value)
        except ValueError:
            return 0.0
    return 0.0


def _load_default_profiles() -> tuple[str, str]:
    from openhumming.workspace.initializer import DEFAULT_AGENT_PROFILE, DEFAULT_USER_PROFILE

    return DEFAULT_AGENT_PROFILE, DEFAULT_USER_PROFILE


def _preview(text: str, limit: int = 160) -> str:
    cleaned = " ".join(text.split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 3].rstrip() + "..."


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as handle:
        handle.bind(("127.0.0.1", 0))
        return int(handle.getsockname()[1])


def _build_demo_server_env(port: int) -> dict[str, str]:
    env = os.environ.copy()
    provider = env.get(DEMO_PROVIDER_ENV, "local").strip() or "local"
    env.update(
        {
            "OPENHUMMING_HOST": "127.0.0.1",
            "OPENHUMMING_PORT": str(port),
            "OPENHUMMING_WORKSPACE_ROOT": str(WORKSPACE_ROOT),
            "OPENHUMMING_SCHEDULER_ENABLED": "false",
            "OPENHUMMING_PROVIDER": provider,
        }
    )
    return env


def _decode_response_payload(response: httpx.Response) -> Any:
    try:
        return response.json()
    except json.JSONDecodeError:
        content_type = response.headers.get("content-type", "unknown")
        body = response.text.strip()
        return {
            "error": "non_json_response",
            "status_code": response.status_code,
            "content_type": content_type,
            "body": body,
        }


if __name__ == "__main__":
    raise SystemExit(main())
