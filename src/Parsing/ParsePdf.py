import re
from collections import Counter
from pathlib import Path

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "documents"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "documents_md"

CHAPTER_PATTERN = re.compile(r"^(\d+)\.\s+(?=[A-ZА-ЯЁ\d«\"(])")
SUBSECTION_PATTERN = re.compile(r"^(\d+\.\d+)\.\s+")
SUBSUBSECTION_PATTERN = re.compile(r"^(\d+\.\d+\.\d+)\.\s+")
LIST_ITEM_PATTERN = re.compile(r"^[-•*−]\s+")
DOT_LEADER_PATTERN = re.compile(r"\.{4,}\s*\d+\s*$")
NAMED_HEADING_PATTERN = re.compile(
    r"^(?:"
    r"приложение(?:\s+[a-zа-яё0-9.-]+)?|"
    r"appendix(?:\s+[a-z0-9.-]+)?|"
    r"attachment|annex|"
    r"лист\s+(?:согласования|регистрации(?:\s+изменений)?)|"
    r"содержание|оглавление|"
    r"table\s+of\s+contents"
    r")\s*$",
    re.IGNORECASE,
)

PAGE_FOOTER_PATTERNS = (
    re.compile(r"^\s*(?:стр\.|page|sheet)\s*\d+\s*(?:из|of|/)\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^\s*-\s*\d+\s*-\s*$"),
    re.compile(r"^\s*\d{1,4}\s*$"),
)

STRUCTURAL_LINE_KINDS = frozenset(
    {"chapter", "subsection", "subsubsection", "heading", "list_item"}
)


def extract_text_from_pdf(pdf_path: Path) -> str:
    with fitz.open(pdf_path) as document:
        pages = [page.get_text().strip() for page in document if page.get_text().strip()]

    if not pages:
        return ""

    pages = [_strip_page_footers(page) for page in pages]

    header_line_count = _detect_repeating_edge_lines(pages, from_start=True)
    footer_line_count = _detect_repeating_edge_lines(pages, from_start=False)

    cleaned_pages: list[str] = []
    for index, page in enumerate(pages):
        if index > 0:
            if header_line_count:
                page = _strip_edge_lines(page, header_line_count, from_start=True)
            if footer_line_count:
                page = _strip_edge_lines(page, footer_line_count, from_start=False)
        cleaned_pages.append(page.strip())

    return "\n\n".join(cleaned_pages)


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _page_lines(page_text: str) -> list[str]:
    return [line.strip() for line in page_text.split("\n") if line.strip()]


def _normalize_for_repeat_match(text: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip().lower()
    return re.sub(r"\b\d+\b", "#", normalized)


def _strip_page_footers(page_text: str) -> str:
    lines = page_text.split("\n")
    while lines:
        candidate = lines[-1].strip()
        if not candidate:
            lines.pop()
            continue
        if any(pattern.match(candidate) for pattern in PAGE_FOOTER_PATTERNS):
            lines.pop()
            continue
        break
    return "\n".join(lines)


def _detect_repeating_edge_lines(
    pages: list[str],
    from_start: bool,
    max_scan_lines: int = 14,
    min_match_ratio: float = 0.45,
) -> int:
    if len(pages) < 2:
        return 0

    sample_pages = pages[1:]
    line_sets = [_page_lines(page) for page in sample_pages]
    if not line_sets:
        return 0

    max_common = min(max(len(lines) for lines in line_sets), max_scan_lines)
    best_length = 0
    threshold = max(2, int(len(sample_pages) * min_match_ratio))

    for length in range(1, max_common + 1):
        signatures = []
        for lines in line_sets:
            block = lines[:length] if from_start else lines[-length:]
            if len(block) < length:
                break
            signatures.append(_normalize_for_repeat_match("\n".join(block)))
        else:
            counter = Counter(signatures)
            most_common_count = counter.most_common(1)[0][1]
            signature = counter.most_common(1)[0][0]
            if most_common_count >= threshold and len(signature) >= 20:
                best_length = length

    return best_length


def _strip_edge_lines(page_text: str, line_count: int, from_start: bool) -> str:
    lines = _page_lines(page_text)
    if line_count <= 0 or not lines:
        return page_text

    if from_start:
        return "\n".join(lines[line_count:])
    return "\n".join(lines[:-line_count])


def _fix_hyphenated_line_breaks(text: str) -> str:
    return re.sub(
        r"(?<=[а-яёa-zА-ЯЁA-Z])-\n(?=[а-яёa-zА-ЯЁA-Z])",
        "",
        text,
    )


def _strip_page_markers(text: str) -> str:
    text = re.sub(r"(?m)^\s*стр\.\s*\d+\s*из\s*\d+\s*$", "", text)
    text = re.sub(r"\s+стр\.\s*\d+\s*из\s*\d+\s*", " ", text)
    return text


def _fix_broken_tokens(text: str) -> str:
    return re.sub(r"([\w/.-]+)-\s*\n\s*([\w/.-]+)", r"\1-\2", text)


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _is_skippable_line(line: str) -> bool:
    return bool(DOT_LEADER_PATTERN.search(line))


def _matches_section_pattern(line: str, pattern: re.Pattern[str]) -> bool:
    return bool(pattern.match(line)) and not _is_skippable_line(line)


def _classify_line(line: str) -> str:
    stripped = line.strip()
    if not stripped or _is_skippable_line(stripped):
        return "skip"
    if NAMED_HEADING_PATTERN.match(stripped):
        return "heading"
    if _matches_section_pattern(stripped, SUBSUBSECTION_PATTERN):
        return "subsubsection"
    if _matches_section_pattern(stripped, SUBSECTION_PATTERN):
        return "subsection"
    if _matches_section_pattern(stripped, CHAPTER_PATTERN):
        return "chapter"
    if LIST_ITEM_PATTERN.match(stripped):
        return "list_item"
    return "text"


def _next_non_empty_line(lines: list[str], start_index: int) -> tuple[str | None, int]:
    index = start_index
    while index < len(lines):
        stripped = lines[index].strip()
        if stripped and _classify_line(stripped) != "skip":
            return stripped, index
        index += 1
    return None, index


def _is_structural_boundary(lines: list[str], blank_index: int) -> bool:
    next_line, _ = _next_non_empty_line(lines, blank_index + 1)
    if next_line is None:
        return True
    return _classify_line(next_line) in STRUCTURAL_LINE_KINDS


def _flush_buffer(buffer: list[str], output: list[str]) -> None:
    if buffer:
        output.append(" ".join(part.strip() for part in buffer if part.strip()))


def _merge_wrapped_lines(text: str) -> list[str]:
    lines = text.split("\n")
    output: list[str] = []
    buffer: list[str] = []

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line:
            if buffer and _is_structural_boundary(lines, index):
                _flush_buffer(buffer, output)
                buffer = []
            continue

        if _is_skippable_line(line):
            continue

        kind = _classify_line(line)
        if kind == "skip":
            continue

        if kind in STRUCTURAL_LINE_KINDS:
            _flush_buffer(buffer, output)
            buffer = [line]
            continue

        buffer.append(line)

    _flush_buffer(buffer, output)
    return output


def _format_markdown_block(blocks: list[str]) -> str:
    formatted: list[str] = []

    for block in blocks:
        stripped = block.strip()
        if not stripped:
            continue

        if NAMED_HEADING_PATTERN.match(stripped):
            formatted.append(f"# {stripped}")
            continue

        if _matches_section_pattern(stripped, SUBSUBSECTION_PATTERN):
            formatted.append(f"### {stripped}")
            continue

        if _matches_section_pattern(stripped, SUBSECTION_PATTERN):
            formatted.append(f"## {stripped}")
            continue

        if _matches_section_pattern(stripped, CHAPTER_PATTERN):
            formatted.append(f"# {stripped}")
            continue

        formatted.append(stripped)

    return "\n\n".join(formatted)


def _split_oversized_blocks(blocks: list[str], max_size: int = 3500) -> list[str]:
    result: list[str] = []

    for block in blocks:
        if len(block) <= max_size:
            result.append(block)
            continue

        start = 0
        while start < len(block):
            end = min(start + max_size, len(block))
            if end < len(block):
                split_at = block.rfind(". ", start, end)
                if split_at > start + max_size // 2:
                    end = split_at + 1
            piece = block[start:end].strip()
            if piece:
                result.append(piece)
            start = end

    return result


def format_extracted_text(text: str) -> str:
    text = _normalize_line_endings(text)
    text = _fix_hyphenated_line_breaks(text)
    text = _fix_broken_tokens(text)
    text = _strip_page_markers(text)
    text = _normalize_whitespace(text)

    blocks = _split_oversized_blocks(_merge_wrapped_lines(text))
    return _format_markdown_block(blocks).strip() + "\n"


def convert_pdf_to_md(pdf_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{pdf_path.stem}.md"
    raw_text = extract_text_from_pdf(pdf_path)
    md_path.write_text(format_extracted_text(raw_text), encoding="utf-8")
    return md_path


def convert_all_pdfs(
    input_dir: Path = DEFAULT_INPUT_DIR,
    output_dir: Path = DEFAULT_OUTPUT_DIR,
) -> list[Path]:
    pdf_files = sorted(input_dir.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(f"PDF-файлы не найдены в каталоге: {input_dir}")

    created_files: list[Path] = []
    for pdf_path in pdf_files:
        md_path = convert_pdf_to_md(pdf_path, output_dir)
        created_files.append(md_path)
        print(f"Создан: {md_path.name}")

    return created_files


if __name__ == "__main__":
    convert_all_pdfs()
