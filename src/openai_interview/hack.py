from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .contracts import ControlPlaneError, HackVerifyRequest, HackVerifyResult
from .settings import settings


class HackGateway:
    def verify(self, req: HackVerifyRequest) -> HackVerifyResult:
        if not settings.enable_hack_verify:
            return HackVerifyResult(
                status="blocked",
                error=ControlPlaneError(
                    code="hack_verify_disabled",
                    message="Set OPENAI_INTERVIEW_ENABLE_HACK_VERIFY=true to run bounded Hack verify.",
                ),
            )
        run_sh = Path(settings.agent_skills_root) / "skills/hack/run.sh"
        if not run_sh.exists():
            return HackVerifyResult(
                status="blocked",
                error=ControlPlaneError(code="hack_missing", message=str(run_sh)),
            )
        argv = [str(run_sh), "verify"]
        if req.artifact_root:
            argv += ["--out", req.artifact_root]
        proc = subprocess.run(argv, text=True, capture_output=True, timeout=90)
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
