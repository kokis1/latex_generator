import argparse
import logging
import sys
from pathlib import Path

from latex_generator.latex.compiler import is_pdflatex_available
from latex_generator.pipeline import PipelineConfig, run


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="latex_generator",
        description="Convert handwritten note images to LaTeX documents.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  latex_generator notes.jpg
  latex_generator notes.jpg --output my_notes.tex
  latex_generator notes.jpg --model llava --retries 5
  latex_generator notes.jpg --debug
        """,
    )

    parser.add_argument(
        "image",
        type=Path,
        help="Path to the handwritten note image (jpg, png, etc.)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help=(
            "Path for the output .tex file. "
            "Defaults to <image_name>.tex in ./output/"
        ),
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default="minicpm-v",
        help="Ollama model to use (default: minicpm-v)",
    )
    parser.add_argument(
        "--retries", "-r",
        type=int,
        default=3,
        help="Max VLM retry attempts per chunk (default: 3)",
    )
    parser.add_argument(
        "--chunks", "-c",
        type=int,
        default=10,
        help="Max number of segments to split the image into (default: 10)",
    )
    parser.add_argument(
        "--debug", "-d",
        action="store_true",
        help="Write preprocessed chunk images to output/debug/ for inspection",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed logging output",
    )

    return parser


def resolve_output_path(image: Path, output: Path | None) -> Path:
    """
    If no output path is given, place the .tex file next to the
    image in ./output/, preserving the image's stem.
    e.g. photos/lecture.jpg -> output/lecture.tex
    """
    if output is not None:
        return output
    return Path("output") / image.with_suffix(".tex").name


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
        level=level,
        stream=sys.stdout,
    )


def validate_args(args: argparse.Namespace) -> None:
    """
    Catch obvious user errors before the pipeline starts,
    so failures are immediate and clear.
    """
    if not args.image.exists():
        print(f"Error: image file not found: {args.image}", file=sys.stderr)
        sys.exit(1)

    if args.image.suffix.lower() not in {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}:
        print(
            f"Warning: '{args.image.suffix}' is an unusual image format. "
            "Proceeding anyway.",
            file=sys.stderr,
        )

    if args.retries < 1:
        print("Error: --retries must be at least 1", file=sys.stderr)
        sys.exit(1)

    if args.chunks < 1:
        print("Error: --chunks must be at least 1", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    configure_logging(args.verbose)
    validate_args(args)

    output_path = resolve_output_path(args.image, args.output)
    config = PipelineConfig(
        model=args.model,
        max_retries=args.retries,
        max_chunks=args.chunks,
        debug=args.debug,
    )

    print(f"Converting {args.image} -> {output_path}")
    print(f"Model: {config.model}  |  Retries: {config.max_retries}  |  Chunks: {config.max_chunks}")

    try:
        result = run(
            image_path=args.image,
            output_path=output_path,
            config=config,
        )
    except RuntimeError as e:
        # RuntimeErrors from check_dependencies() are user-facing —
        # print cleanly without a traceback
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        sys.exit(130)

    print(f"\n{result.summary}")

    if result.success:
        print(f"\nDone. Output written to: {result.output_path}")
        sys.exit(0)
    else:
        print(
            f"\nCompleted with failures. "
            f"Review % [CONVERSION FAILED] comments in {result.output_path}",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()