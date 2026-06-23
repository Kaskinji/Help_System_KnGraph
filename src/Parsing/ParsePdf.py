from pathlib import Path

import fitz


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_DIR = PROJECT_ROOT / "documents"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "documents_md"


def extract_text_from_pdf(pdf_path: Path) -> str:
    pages: list[str] = []

    with fitz.open(pdf_path) as document:
        for page in document:
            text = page.get_text().strip()
            if text:
                pages.append(text)

    return "\n\n".join(pages)


def convert_pdf_to_md(pdf_path: Path, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)

    md_path = output_dir / f"{pdf_path.stem}.md"
    text = extract_text_from_pdf(pdf_path)

    md_path.write_text(text, encoding="utf-8")
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
