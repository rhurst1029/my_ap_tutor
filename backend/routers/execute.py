"""
Java code execution endpoint.
Accepts student source code, compiles with javac, runs with java,
returns stdout/stderr. Hard timeout: 8 seconds total.
"""
import subprocess, tempfile, os, re
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

TIMEOUT_SECONDS = 8


class ExecuteRequest(BaseModel):
    source_code: str
    class_name: str = "Solution"


class ExecuteResponse(BaseModel):
    stdout: str
    stderr: str
    compile_errors: list[str]
    passed: bool
    timed_out: bool


def _extract_class_name(source: str) -> str:
    """Pull the public class name from source so the file name matches."""
    match = re.search(r'public\s+class\s+(\w+)', source)
    return match.group(1) if match else "Solution"


@router.post("/", response_model=ExecuteResponse)
async def execute_java(req: ExecuteRequest):
    class_name = _extract_class_name(req.source_code)

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, f"{class_name}.java")
        with open(src_path, "w") as f:
            f.write(req.source_code)

        # ── Compile ──────────────────────────────────────────────────────────
        try:
            compile_result = subprocess.run(
                ["javac", src_path],
                capture_output=True, text=True,
                timeout=TIMEOUT_SECONDS,
                cwd=tmpdir,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                stdout="", stderr="Compilation timed out.",
                compile_errors=["Compilation timed out."],
                passed=False, timed_out=True,
            )
        except FileNotFoundError:
            return ExecuteResponse(
                stdout="", stderr="javac not found. Is Java installed?",
                compile_errors=["javac not found."],
                passed=False, timed_out=False,
            )

        if compile_result.returncode != 0:
            raw_errors = compile_result.stderr.strip()
            # Strip the temp path prefix so error messages are clean
            clean = raw_errors.replace(tmpdir + "/", "")
            errors = [line for line in clean.splitlines() if line.strip()]
            return ExecuteResponse(
                stdout="", stderr=clean,
                compile_errors=errors,
                passed=False, timed_out=False,
            )

        # ── Run ──────────────────────────────────────────────────────────────
        try:
            run_result = subprocess.run(
                ["java", "-cp", tmpdir, class_name],
                capture_output=True, text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            return ExecuteResponse(
                stdout="", stderr="Execution timed out (infinite loop?).",
                compile_errors=[],
                passed=False, timed_out=True,
            )

        return ExecuteResponse(
            stdout=run_result.stdout,
            stderr=run_result.stderr,
            compile_errors=[],
            passed=run_result.returncode == 0,
            timed_out=False,
        )
