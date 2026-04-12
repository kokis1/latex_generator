from dataclasses import dataclass, field
from pathlib import Path
from latex_generator.latex.templates import build_full_document
import re

def sanitise_fragment(fragment: str) -> str:
    """
    Strip any preamble or document environment tags the model
    outputs despite instructions. Operates line by line.
    """
    # Patterns that must never appear in a body fragment
    forbidden_starts = (
        r"\documentclass",
        r"\usepackage",
        r"\begin{document}",
        r"\end{document}",
        r"\maketitle",
        r"\title",
        r"\author",
        r"\date",
    )
    clean_lines = []
    for line in fragment.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(p) for p in forbidden_starts):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()

@dataclass
class DocumentBuilder:
    """
    Accumulates LaTeX fragments into a growing document.
    Keeps body and full document separate so the compiler
    always gets a complete, compilable string without the
    builder needing to know about the preamble internals.
    """
    fragments: list[str] = field(default_factory=list)
    failed_chunks: list[int] = field(default_factory=list)

    @property
    def body(self) -> str:
        return "\n\n".join(self.fragments)

    @property
    def full_document(self) -> str:
        return build_full_document(self.body)

    def append(self, fragment: str, chunk_index: int) -> None:
        """Add a successfully validated fragment to the document."""
        cleaned = sanitise_fragment(fragment.strip())
        if cleaned:
            self.fragments.append(cleaned)

    def append_placeholder(self, chunk_index: int, reason: str) -> None:
        """
        Called when a chunk exhausts all retries. Inserts a comment
        so the document still compiles and the failure is visible.
        """
        self.failed_chunks.append(chunk_index)
        self.fragments.append(
            f"% [CONVERSION FAILED — chunk {chunk_index}: {reason}]"
        )

    def save(self, output_path: str | Path) -> Path:
        """Write the final .tex file to disk."""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.full_document, encoding="utf-8")
        return output_path

    def summary(self) -> str:
        """Human-readable conversion summary for CLI output."""
        total = len(self.fragments)
        failed = len(self.failed_chunks)
        succeeded = total - failed
        lines = [
            f"Chunks converted:  {succeeded}/{total}",
        ]
        if self.failed_chunks:
            lines.append(
                f"Failed chunk indices: {self.failed_chunks}"
            )
            lines.append(
                "  -> Review % [CONVERSION FAILED] comments in output."
            )
        return "\n".join(lines)