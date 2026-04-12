# The system prompt sets the VLM's behaviour for the entire session.
# Keeping it strict ("ONLY valid LaTeX") reduces the model hallucinating
# explanatory prose around its output.
SYSTEM_PROMPT = """You are an expert LaTeX transcription assistant.
You convert images of handwritten notes into valid LaTeX fragments.

Rules:
- Output ONLY raw LaTeX. No explanations, no markdown code fences, no preamble.
- Inline math uses $...$. Display math uses \\[...\\].
- Multi-line equations use the align environment.
- If text appears underlined or circled, treat it as a section heading: \\section{...}
- If you see a drawn figure or diagram you cannot transcribe, output exactly:
  % [DIAGRAM: brief description]
- If a region is illegible, output exactly:
  % [ILLEGIBLE]
- Never invent content. If uncertain, prefer % [ILLEGIBLE] over a guess."""


# Used for the first chunk — no prior context yet.
INITIAL_PROMPT = """Convert the handwritten content in this image to a LaTeX fragment.
Follow your system instructions exactly."""


# Used for subsequent chunks — gives the model context of what came before,
# which helps it maintain consistent notation and heading hierarchy.
CONTINUATION_PROMPT = """Convert the handwritten content in this image to a LaTeX fragment.

Here is the LaTeX generated so far (for context only — do not repeat it):
--- BEGIN CONTEXT ---
{context}
--- END CONTEXT ---

Continue from where the document left off. Output only the new fragment."""


# Used when a fragment caused a compilation error.
# Feeding the error back lets the model self-correct without a full retry.
CORRECTION_PROMPT = """Your previous LaTeX fragment caused a compilation error.

Fragment that failed:
--- BEGIN FRAGMENT ---
{fragment}
--- END FRAGMENT ---

Compiler error:
--- BEGIN ERROR ---
{error}
--- END ERROR ---

Fix the fragment so it compiles correctly.
Output only the corrected LaTeX fragment, nothing else."""