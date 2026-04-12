import ollama
import cv2
import numpy as np
import tempfile
from pathlib import Path

from latex_generator.VLM.prompts import (
    SYSTEM_PROMPT,
    INITIAL_PROMPT,
    CONTINUATION_PROMPT,
    CORRECTION_PROMPT,
)


class VLMClient:
    def __init__(self, model: str = "minicpm-v", timeout: int = 120):
        self.model = model
        self.timeout = timeout
        self.check_model_available()

    def check_model_available(self) -> None:
        available = [m.model for m in ollama.list().models]
        # Ollama appends ':latest' if no tag is specified, so normalise both sides
        available_stems = [name.split(":")[0] for name in available]
        if self.model.split(":")[0] not in available_stems:
            raise RuntimeError(
                f"Model '{self.model}' not found. "
                f"Run: ollama pull {self.model}\n"
                f"Available models: {available}"
            )

    def transcribe(
        self,
        image: np.ndarray,
        context: str = "",
        error: str = "",
    ) -> str:
        """
        Main entry point. Accepts a numpy array (from OpenCV) and returns
        a raw LaTeX fragment string.

        Args:
            image:   The chunk image as a numpy array.
            context: LaTeX accumulated so far (for continuation prompt).
            error:   Compiler error from previous attempt (for correction prompt).
        """
        image_path = self.write_temp_image(image)
        prompt = self.build_prompt(context, error)

        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": prompt,
                        "images": [str(image_path)],
                    },
                ],
            )
            assert response.message.content != None, "Unexpected empty message content"
            return self.clean_response(response.message.content)
        finally:
            image_path.unlink(missing_ok=True)  # clean up temp file

    def build_prompt(self, context: str, error: str) -> str:
        if error:
            # Correction mode — the fragment that failed is in the error string
            return CORRECTION_PROMPT.format(
                fragment=context,   # reuse context field for the failed fragment
                error=error,
            )
        if context:
            # Trim context to last 800 chars — enough for notation consistency
            # without overloading the model's context window
            trimmed = context[-800:]
            return CONTINUATION_PROMPT.format(context=trimmed)
        return INITIAL_PROMPT

    def write_temp_image(self, image: np.ndarray) -> Path:
        """
        Ollama's Python SDK takes a file path, not raw bytes.
        We write to a temp file and clean up after the call.
        """
        tmp = tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        )
        cv2.imwrite(tmp.name, image)
        return Path(tmp.name)

    @staticmethod
    def clean_response(text: str) -> str:
        """
        Strip any markdown fencing the model adds despite instructions.
        Models sometimes wrap output in ```latex ... ``` regardless.
        """
        text = text.strip()
        # Remove opening fence (with or without language tag)
        if text.startswith("```"):
            text = text[text.index("\n") + 1:] if "\n" in text else text[3:]
        # Remove closing fence
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()