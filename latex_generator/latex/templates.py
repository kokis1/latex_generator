PREAMBLE = r"""\documentclass[12pt, a4paper]{article}

\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{amsthm}
\usepackage{graphicx}
\usepackage{geometry}
\usepackage{parskip}
\usepackage{microtype}

\geometry{margin=2.5cm}

\title{Converted Notes}
\author{}
\date{\today}"""

DOCUMENT_BEGIN = r"\begin{document}"
DOCUMENT_MAKETITLE = r"\maketitle"
DOCUMENT_END = r"\end{document}"


def build_full_document(body: str) -> str:
    """Assembles a complete compilable .tex string from a body fragment."""
    text = "\n".join([
        PREAMBLE,
        DOCUMENT_BEGIN,
        DOCUMENT_MAKETITLE,
        body,
        DOCUMENT_END,
    ])
    return text