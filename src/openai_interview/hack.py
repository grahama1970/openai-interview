"""Bounded Hack skill gateway for safety preflight and local SAST scans."""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .contracts import ControlPlaneError, HackAuditRequest, HackAuditResult, HackVerifyRequest, HackVerifyResult
from .settings import settings


class HackGateway:
    def __init__(self, memory: Any | None = None) -> None:
        self.memory = memory

    def _run_sh(self) -> Path:
        return Path(settings.agent_skills_root) / "skills/hack/run.sh"

    def _env(self) -> dict[str, str]:
        env = os.environ.copy()
        env.pop("VIRTUAL_ENV", None)
        env["PATH"] = "/home/graham/.local/bin:/usr/local/bin:/usr/bin:/bin"
        return env

    def verify(self, req: HackVerifyRequest) -> HackVerifyResult:
        run_sh = self._run_sh()
        if not settings.enable_hack_verify:
            return HackVerifyResult(
                status="blocked",
                error=ControlPlaneError(
                    code="hack_verify_disabled",
                    message="Set OPENAI_INTERVIEW_ENABLE_HACK_VERIFY=true to run bounded Hack verify.",
                ),
            )
        if not run_sh.exists():
            return HackVerifyResult(status="blocked", error=ControlPlaneError(code="hack_missing", message=str(run_sh)))
        argv = [str(run_sh), "verify"]
        if req.artifact_root:
            argv += ["--out", req.artifact_root]
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=90, env=self._env())
        receipt = None
        try:
            receipt = json.loads(proc.stdout).get("receipt")
        except Exception:
            pass
        return HackVerifyResult(
            status="pass" if proc.returncode == 0 else "fail",
            receipt=receipt,
            stdout_tail=proc.stdout[-2000:],
            stderr_tail=proc.stderr[-2000:],
            error=None if proc.returncode == 0 else ControlPlaneError(code="hack_verify_failed", message=f"hack verify exited {proc.returncode}"),
        )

    def audit(self, req: HackAuditRequest) -> HackAuditResult:
        run_sh = self._run_sh()
        if not settings.enable_hack_audit:
            return HackAuditResult(
                status="blocked",
                target_kind=req.target_kind,
                tool=req.tool,
                command=[],
                error=ControlPlaneError(
                    code="hack_audit_disabled",
                    message="Set OPENAI_INTERVIEW_ENABLE_HACK_AUDIT=true to run bounded Hack audit.",
                ),
            )
        if not run_sh.exists():
            return HackAuditResult(status="blocked", target_kind=req.target_kind, tool=req.tool, command=[], error=ControlPlaneError(code="hack_missing", message=str(run_sh)))

        with tempfile.TemporaryDirectory(prefix="openai-interview-hack-") as tmp:
            target = self._target(req.target_kind, Path(tmp))
            output = Path(tmp) / "hack-audit.json"
            durable_receipt = Path("receipts/agentic/hack-audit-receipt.json")
            durable_receipt.parent.mkdir(parents=True, exist_ok=True)
            argv = [
                str(run_sh), "audit", str(target),
                "--tool", req.tool,
                "--severity", req.severity,
                "--no-recall",
                "--output", str(output),
                "--receipt-out", str(durable_receipt),
            ]
            argv.append("--memory-store" if req.persist_to_memory else "--no-memory-store")
            argv += ["--memory-collection", req.memory_collection]
            proc = subprocess.run(argv, text=True, capture_output=True, timeout=settings.hack_timeout_seconds, env=self._env())
            receipt = self._read_receipt(durable_receipt)
            summary = receipt.get("summary", {})
            status = "pass" if proc.returncode == 0 and summary.get("finding_count", 0) > 0 else "blocked" if proc.returncode == 0 else "fail"
            return HackAuditResult(
                status=status,
                target_kind=req.target_kind,
                tool=req.tool,
                command=argv,
                finding_count=int(summary.get("finding_count", 0)),
                high_count=int(summary.get("high_count", 0)),
                cwes=list(summary.get("cwes", [])),
                output_path=str(durable_receipt),
                receipt_ref=(receipt.get("memory") or {}).get("store_ref"),
                stdout_tail=proc.stdout[-2000:],
                stderr_tail=proc.stderr[-2000:],
                error=None if proc.returncode == 0 else ControlPlaneError(code="hack_audit_failed", message=f"hack audit exited {proc.returncode}"),
            )

    def _target(self, target_kind: str, tmp: Path) -> Path:
        if target_kind == "self":
            return Path(__file__).resolve().parents[2]
        sample = tmp / "insecure.py"
        sample.write_text(
            "import subprocess\n\n"
            "def run(user_input):\n"
            "    return subprocess.run('echo ' + user_input, shell=True)\n"
        )
        return sample

    def _read_receipt(self, path: Path) -> dict[str, Any]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
