#!/usr/bin/env python3
"""Windows-friendly wrapper around skill-creator eval/loop scripts.

This keeps the original skill-creator logic, but patches the Claude CLI calls
to invoke the installed CLI entrypoint directly via Node instead of relying on
`claude` being executable inside Python subprocesses on Windows.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import uuid
import webbrowser
from pathlib import Path


SKILL_CREATOR_ROOT = Path(r"C:\Users\toqu\.agents\skills\skill-creator")
CLAUDE_CLI_JS = Path(
    r"C:\Users\toqu\AppData\Roaming\npm\node_modules\@anthropic-ai\claude-code\cli.js"
)

sys.path.insert(0, str(SKILL_CREATOR_ROOT))

from scripts.generate_report import generate_html  # noqa: E402
from scripts.run_eval import find_project_root, run_eval  # noqa: E402
from scripts.run_loop import run_loop  # noqa: E402
import scripts.improve_description as improve_mod  # noqa: E402
import scripts.run_eval as run_eval_mod  # noqa: E402


def _base_claude_cmd() -> list[str]:
    return [
        "node",
        str(CLAUDE_CLI_JS),
        "--permission-mode",
        "bypassPermissions",
    ]


def _env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def patched_run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            "---\n"
            "description: |\n"
            f"  {indented_desc}\n"
            "---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content, encoding="utf-8")

        cmd = _base_claude_cmd() + [
            "-p",
            query,
            "--output-format",
            "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])
        try:
            completed = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=project_root,
                env=_env(),
                timeout=timeout,
            )
            stdout = completed.stdout or ""
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")

        triggered = False
        pending_tool_name = None
        accumulated_json = ""

        for raw_line in stdout.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue

            if event.get("type") == "stream_event":
                se = event.get("event", {})
                se_type = se.get("type", "")

                if se_type == "content_block_start":
                    cb = se.get("content_block", {})
                    if cb.get("type") == "tool_use":
                        tool_name = cb.get("name", "")
                        if tool_name in ("Skill", "Read"):
                            pending_tool_name = tool_name
                            accumulated_json = ""
                        else:
                            return False

                elif se_type == "content_block_delta" and pending_tool_name:
                    delta = se.get("delta", {})
                    if delta.get("type") == "input_json_delta":
                        accumulated_json += delta.get("partial_json", "")
                        if clean_name in accumulated_json:
                            return True

                elif se_type in ("content_block_stop", "message_stop"):
                    if pending_tool_name and clean_name in accumulated_json:
                        return True

            elif event.get("type") == "assistant":
                message = event.get("message", {})
                for content_item in message.get("content", []):
                    if content_item.get("type") != "tool_use":
                        continue
                    tool_name = content_item.get("name", "")
                    tool_input = content_item.get("input", {})
                    if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                        return True
                    if tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                        return True

            elif event.get("type") == "result":
                return triggered

        return triggered
    finally:
        if command_file.exists():
            command_file.unlink()


def patched_call_claude(prompt: str, model: str | None, timeout: int = 300) -> str:
    cmd = _base_claude_cmd() + ["-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])

    result = subprocess.run(
        cmd,
        input=prompt,
        capture_output=True,
        text=True,
        env=_env(),
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"claude -p exited {result.returncode}\nstderr: {result.stderr}"
        )
    return result.stdout


run_eval_mod.run_single_query = patched_run_single_query
improve_mod._call_claude = patched_call_claude


def main() -> None:
    parser = argparse.ArgumentParser(description="Windows wrapper for skill-creator")
    parser.add_argument("--eval-set", required=True)
    parser.add_argument("--skill-path", required=True)
    parser.add_argument("--description", default=None)
    parser.add_argument("--num-workers", type=int, default=4)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--runs-per-query", type=int, default=1)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--max-iterations", type=int, default=5)
    parser.add_argument("--holdout", type=float, default=0.4)
    parser.add_argument("--model", default=None)
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--report", default="none")
    parser.add_argument("--results-dir", default=None)
    parser.add_argument("--eval-only", action="store_true")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        raise SystemExit(f"No SKILL.md found at {skill_path}")

    if args.eval_only:
        name, original_description, _ = run_eval_mod.parse_skill_md(skill_path)
        description = args.description or original_description
        output = run_eval(
            eval_set=eval_set,
            skill_name=name,
            description=description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            project_root=find_project_root(),
            runs_per_query=args.runs_per_query,
            trigger_threshold=args.trigger_threshold,
            model=args.model,
        )
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return

    report_path = None
    if args.report != "none":
        if args.report == "auto":
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            report_path = Path(tempfile.gettempdir()) / f"skill_description_report_{skill_path.name}_{timestamp}.html"
        else:
            report_path = Path(args.report)
        report_path.write_text(
            "<html><body><h1>Starting optimization loop...</h1><meta http-equiv='refresh' content='5'></body></html>",
            encoding="utf-8",
        )
        webbrowser.open(str(report_path))

    results_dir = None
    if args.results_dir:
        timestamp = time.strftime("%Y-%m-%d_%H%M%S")
        results_dir = Path(args.results_dir) / timestamp
        results_dir.mkdir(parents=True, exist_ok=True)

    output = run_loop(
        eval_set=eval_set,
        skill_path=skill_path,
        description_override=args.description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        max_iterations=args.max_iterations,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        holdout=args.holdout,
        model=args.model,
        verbose=args.verbose,
        live_report_path=report_path,
        log_dir=(results_dir / "logs") if results_dir else None,
    )

    output_json = json.dumps(output, indent=2, ensure_ascii=False)
    print(output_json)

    if results_dir:
        (results_dir / "results.json").write_text(output_json, encoding="utf-8")
        if report_path:
            (results_dir / "report.html").write_text(
                generate_html(output, auto_refresh=False, skill_name=skill_path.name),
                encoding="utf-8",
            )

    if report_path:
        report_path.write_text(
            generate_html(output, auto_refresh=False, skill_name=skill_path.name),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
