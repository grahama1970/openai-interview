"""Bounded Hack skill gateway for safety preflight and local SAST scans."""
from __future__ import annotations

import hashlib
import json
import os
import re
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
            return HackVerifyResult(
                status="blocked",
                error=ControlPlaneError(code="hack_missing", message=str(run_sh)),
            )
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
            error=None if proc.returncode == 0 else ControlPlaneError(
                code="hack_verify_failed",
                message=f"hack verify exited {proc.returncode}",
            ),
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
            return HackAuditResult(
                status="blocked",
                target_kind=req.target_kind,
                tool=req.tool,
                command=[],
                error=ControlPlaneError(code="hack_missing", message=str(run_sh)),
            )

        with tempfile.TemporaryDirectory(prefix="openai-interview-hack-") as tmp:
            target = self._target(req.target_kind, Path(tmp))
            output = Path(tmp) / "hack-audit.json"
            argv = [str(run_sh), "audit", str(target), "--tool", req.tool, "--severity", req.severity, "--no-recall", "--output", str(output)]
            proc = subprocess.run(argv, text=True, capture_output=True, timeout=settings.hack_timeout_seconds, env=self._env())
            parsed = self._parse_output(output)
            durable_output = Path("receipts/agentic/hack-audit-output.json")
            durable_output.parent.mkdir(parents=True, exist_ok=True)
            durable_output.write_text(json.dumps(parsed, indent=2))
            text = "\n".join(v for v in (parsed.get("semgrep"), parsed.get("bandit")) if isinstance(v, str))
            finding_count = text.count(">> Issue:") + text.count("Command execution sink detected")
            high_count = text.count("Severity: High") + text.count("severity: ERROR")
            cwes = sorted(set(re.findall(r"CWE-\d+", text)))
            status = "pass" if proc.returncode == 0 and finding_count > 0 else "blocked" if proc.returncode == 0 else "fail"
            receipt_ref = self._store_audit(req, status, finding_count, high_count, cwes, argv, text)
            return HackAuditResult(
                status=status,
                target_kind=req.target_kind,
                tool=req.tool,
                command=argv,
                finding_count=finding_count,
                high_count=high_count,
                cwes=cwes,
                output_path=str(durable_output),
                receipt_ref=receipt_ref,
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

    def _parse_output(self, output: Path) -> dict[str, Any]:
        if not output.exists():
            return {}
        try:
            return json.loads(output.read_text())
        except json.JSONDecodeError:
            return {}

    def _store_audit(
        self,
        req: HackAuditRequest,
        status: str,
        finding_count: int,
        high_count: int,
        cwes: list[str],
        argv: list[str],
        text: str,
    ) -> str | None:
        if not req.persist_to_memory or self.memory is None:
            return None
        digest = hashlib.sha256(text.encode()).hexdigest()[:16]
        key = f"hack-audit-{req.target_kind}-{req.tool}-{digest}"
        doc = {
            "_key": key,
            "schema": "openai_interview.hack_audit_receipt.v1",
            "kind": "openai_interview_hack_audit_receipt",
            "status": status,
            "target_kind": req.target_kind,
            "tool": req.tool,
            "finding_count": finding_count,
            "high_count": high_count,
            "cwes": cwes,
            "command": argv,
            "classification": req.classification,
            "tags": ["openai-interview", "hack", "cyber-safety"],
            "retrieval_text": f"Hack audit {req.target_kind} {req.tool} found {finding_count} findings {', '.join(cwes)}",
            "stdout_excerpt": text[:4000],
        }
        return self.memory.store(req.memory_collection, doc)
