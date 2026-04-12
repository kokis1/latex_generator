import subprocess
import tempfile
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CompileResult:
    ok: bool
    errors: list[str]
    raw_log: str

    def first_error(self) -> str:
        """Convenience for passing the most relevant error to the VLM."""
        return self.errors[0] if self.errors else ""


def compile(tex_content: str) -> CompileResult:
    """
    Writes tex_content to a temp directory, runs pdflatex,
    and returns a structured result. The temp directory is
    always cleaned up, success or failure.
    """
    with tempfile.TemporaryDirectory() as tmp:
        tex_file = Path(tmp) / "document.tex"
        tex_file.write_text(tex_content, encoding="utf-8")

        result = subprocess.run(
            [
                "pdflatex",
                "-interaction=nonstopmode",
                "-halt-on-error",
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            cwd=tmp,
        )

        log = result.stdout + result.stderr
        ok = result.returncode == 0
        errors = parse_errors(log) if not ok else []

        return CompileResult(ok=ok, errors=errors, raw_log=log)


def parse_errors(log: str) -> list[str]:
    """
    Extracts human-readable error lines from pdflatex output.
    pdflatex errors start with '!' and are followed by the
    offending line on the next non-empty line.
    """
    errors = []
    lines = log.splitlines()

    for i, line in enumerate(lines):
        if line.startswith("!"):
            error_msg = line[1:].strip()
            # Grab the context line if present
            for j in range(i + 1, min(i + 4, len(lines))):
                context = lines[j].strip()
                if context and not context.startswith("!"):
                    error_msg += f" — near: {context}"
                    break
            errors.append(error_msg)

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for e in errors:
        if e not in seen:
            seen.add(e)
            unique.append(e)

    return unique


def is_pdflatex_available() -> bool:
    """Check at startup that pdflatex is on PATH."""
    try:
        subprocess.run(
            ["pdflatex", "--version"],
            capture_output=True,
            check=True,
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False