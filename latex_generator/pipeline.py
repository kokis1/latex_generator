import logging
from dataclasses import dataclass
from pathlib import Path

from latex_generator.preprocess.image import load_and_clean
from latex_generator.preprocess.segment import segment, save_chunks
from latex_generator.VLM.client import VLMClient
from latex_generator.latex.builder import DocumentBuilder
from latex_generator.latex.compiler import compile, is_pdflatex_available
from latex_generator.latex.templates import build_full_document

logger = logging.getLogger(__name__)


@dataclass
class PipelineConfig:
    model: str = "minicpm-v"
    max_retries: int = 3
    max_chunks: int = 10
    context_chars: int = 800
    debug: bool = False
    debug_dir: Path = Path("output/debug")


@dataclass
class PipelineResult:
    output_path: Path
    success: bool
    summary: str


def run(
    image_path: str | Path,
    output_path: str | Path,
    config: PipelineConfig = PipelineConfig(),
) -> PipelineResult:
    """
    Full conversion pipeline. Accepts an image path, writes a .tex
    file to output_path, and returns a structured result.
    """
    image_path = Path(image_path)
    output_path = Path(output_path)

    check_dependencies(config.model)

    logger.info(f"Loading image: {image_path}")
    img = load_and_clean(image_path)

    logger.info("Segmenting into chunks...")
    chunks = segment(img, max_chunks=config.max_chunks)
    logger.info(f"  {len(chunks)} chunks found")

    if config.debug:
        saved = save_chunks(chunks, config.debug_dir)
        logger.debug(f"  Debug chunks written to {config.debug_dir}")

    client = VLMClient(model=config.model)
    builder = DocumentBuilder()

    for chunk in chunks:
        logger.info(f"Converting chunk {chunk.index + 1}/{len(chunks)}...")
        fragment, error = convert_chunk(
            chunk=chunk,
            client=client,
            builder=builder,
            max_retries=config.max_retries,
        )

        if fragment is not None:
            builder.append(fragment, chunk.index)
            logger.info(f"  Chunk {chunk.index + 1} succeeded")
        else:
            builder.append_placeholder(chunk.index, reason=error)
            logger.warning(
                f"  Chunk {chunk.index + 1} failed after "
                f"{config.max_retries} retries: {error}"
            )

    output_path = builder.save(output_path)
    summary = builder.summary()

    logger.info(f"Output written to {output_path}")
    logger.info(summary)

    return PipelineResult(
        output_path=output_path,
        success=not builder.failed_chunks,
        summary=summary,
    )


def convert_chunk(
    chunk,
    client: VLMClient,
    builder: DocumentBuilder,
    max_retries: int,
) -> tuple[str | None, str]:
    last_error = ""
    last_fragment = ""

    for attempt in range(max_retries):
        if attempt == 0:
            fragment = client.transcribe(
                image=chunk.image,
                context=builder.body,
            )
        else:
            fragment = client.transcribe(
                image=chunk.image,
                context=last_fragment,
                error=last_error,
            )

        # ADD THIS — lets us see exactly what the model returns
        logger.debug(f"--- RAW VLM OUTPUT (chunk {chunk.index}, attempt {attempt}) ---")
        logger.debug(fragment)
        logger.debug(f"--- END RAW OUTPUT ---")

        candidate = builder.body + "\n\n" + fragment
        result = compile(build_full_document(candidate))

        if result.ok:
            return fragment, ""

        last_fragment = fragment
        last_error = result.first_error()

        # ADD THIS — lets us see the compiler error clearly
        logger.debug(f"--- COMPILER ERROR ---")
        logger.debug(last_error)
        logger.debug(f"--- END COMPILER ERROR ---")

    return None, last_error


def check_dependencies(model: str) -> None:
    """
    Validates that all external tools are present before starting.
    Raises clearly rather than failing mid-conversion.
    """
    if not is_pdflatex_available():
        raise RuntimeError(
            "pdflatex not found on PATH. "
            "Install MacTeX: brew install --cask mactex-no-gui"
        )

    # VLMClient checks model availability in its own __init__,
    # but we do a quick import check here to catch missing ollama
    # installation before we've done any image work
    try:
        import ollama
    except ImportError:
        raise RuntimeError(
            "ollama package not installed. "
            "Run: pip install ollama"
        )