SYSTEM_PROMPT = "You are a LaTeX transcription assistant."

INSTRUCTION_BLOCK = """Convert the handwritten content in this image to a LaTeX body fragment.

Critical rules:
- Output ONLY raw LaTeX body content.
- Do NOT output \\documentclass, \\usepackage, \\begin{{document}}, \\end{{document}}.
- No explanations, no markdown fences, no preamble of any kind.
- Inline math: $...$
- Display math: \\[...\\]
- Multi-line equations: align environment
- Underlined or circled text: \\section{{...}}
- Drawn figures: % [DIAGRAM: description]
- Illegible content: % [ILLEGIBLE]

Example of correct output:
\\section{{Newton's Laws}}
The first law states that $F = ma$.
\\[
    F = ma
\\]"""


INITIAL_PROMPT = f"""{INSTRUCTION_BLOCK}

Transcribe the image now. Output only LaTeX, starting immediately."""


CONTINUATION_PROMPT = f"""{INSTRUCTION_BLOCK}

Document so far (do not repeat this):
--- BEGIN CONTEXT ---
{{context}}
--- END CONTEXT ---

Continue transcribing from where the document left off. Output only LaTeX."""


CORRECTION_PROMPT = f"""{INSTRUCTION_BLOCK}

Your previous fragment caused a compiler error.

Failed fragment:
--- BEGIN FRAGMENT ---
{{fragment}}
--- END FRAGMENT ---

Compiler error:
--- BEGIN ERROR ---
{{error}}
--- END ERROR ---

Output the corrected LaTeX fragment only."""