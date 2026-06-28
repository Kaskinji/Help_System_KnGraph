import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

# Конфигурация
ROOT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = ROOT_DIR / "documents_md"
OUTPUT_DIR = ROOT_DIR / "chunk_extraction" / "chunks"
LLM_LOG_PATH = SCRIPT_DIR / "llm_responses.log"
CHUNK_TARGET_SIZE = 1200
MAX_PART_SIZE = 12000
MIN_CHUNK_SIZE = 300
MODEL = "poolside/laguna-m.1:free"
SUBSECTION_PATTERN = re.compile(r"(?m)^##\s+(\d+\.\d+)\.\s+")
SECTION_PATTERN = re.compile(r"(?m)^#{1,3}\s+(\d+(?:\.\d+)*\.)\s+")
MAIN_BODY_START_PATTERN = re.compile(r"(?m)^#\s+(\d+)\.\s+(?=[A-ZА-ЯЁ«\"])")
APPENDIX_PATTERN = re.compile(
    r"(?m)^#\s+(?:Лист\s+согласования|Лист\s+регистрации(?:\s+изменений)?)\s*$",
    re.IGNORECASE,
)
DOCUMENT_ID_PATTERN = re.compile(
    r"СМК[-\s]*ПИ[-\s]*[\d.-]+|РП\s+ГИА\s+\d+",
    re.IGNORECASE,
)

CHUNKING_PROMPT = """Раздели фрагмент нормативного или учебно-методического документа на смысловые чанки для поиска по базе знаний.

ВАЖНЫЕ ПРАВИЛА:
1. ГРУППИРУЙ логически связанные пункты в один чанк. Не разбивай по каждому нумерованному пункту, если они относятся к одной теме.
2. Каждый чанк должен быть самодостаточным и иметь смысл без контекста.
3. Ориентировочный размер чанка: 800-2000 символов.
4. Не разрывай нумерованные пункты, абзацы и элементы списков.
5. Сохраняй иерархию: если пункт зависит от предыдущего - объединяй их.
6. Служебные фрагменты (подписи, титулы) пропускай.

Для каждого чанка укажи:
- id: короткий латинский идентификатор (например p_1_12)
- title: краткий заголовок на русском
- abstract: одно предложение с сутью чанка
- size: число символов в content
- content: текст чанка

Верни JSON:
{{"chunks": [{{"id": "...", "title": "...", "abstract": "...", "size": N, "content": "..."}}]}}

Текст для обработки:
{text}"""


def load_env_file() -> None:
    """Загружает переменные из .env в корне проекта (не перезаписывает уже заданные)."""
    env_path = ROOT_DIR / ".env"
    if not env_path.is_file():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


def get_api_key() -> str:
    load_env_file()
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError(
            "Не задан OPENROUTER_API_KEY. "
            "Задайте переменную окружения или добавьте OPENROUTER_API_KEY=... в файл .env в корне проекта."
        )
    return api_key


def read_markdown(md_path: Path) -> str:
    with open(md_path, encoding="utf-8") as file:
        return file.read()


def prepare_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"(?<=[а-яёa-zА-ЯЁA-Z])-\n(?=[а-яёa-zА-ЯЁA-Z])", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def normalize_for_compare(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n+", "\n", text)
    return text.strip()


def extract_document_id(text: str, source_name: str) -> str:
    head = re.sub(r"-\s*\n\s*", "-", text[:3000])
    match = DOCUMENT_ID_PATTERN.search(head)
    if match:
        return re.sub(r"\s+", " ", match.group(0)).strip()
    return Path(source_name).stem


def extract_indexable_body(text: str) -> str:
    """Оставляет основной текст документа без титула и приложений."""
    body_start = MAIN_BODY_START_PATTERN.search(text)
    if not body_start:
        return text.strip()

    body = text[body_start.start() :].strip()
    appendix = APPENDIX_PATTERN.search(body)
    if appendix:
        body = body[: appendix.start()].strip()
    return body


def split_into_sections(text: str) -> List[str]:
    """Разбивает текст по подпунктам ## N.N. (или по # / ##, если подпунктов нет)."""
    matches = list(SUBSECTION_PATTERN.finditer(text))
    if not matches:
        matches = list(SECTION_PATTERN.finditer(text))
    if not matches:
        return [text] if text else []

    sections: List[str] = []
    for index, match in enumerate(matches):
        start = match.start()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        section = text[start:end].strip()
        if section:
            sections.append(section)

    return sections


def pack_sections(sections: List[str], max_size: int) -> List[str]:
    """Объединяет соседние секции до max_size, не разрывая атомарные секции."""
    if not sections:
        return []

    parts: List[str] = []
    current = ""

    for section in sections:
        if len(section) > max_size:
            if current:
                parts.append(current)
                current = ""
            parts.append(section)
            continue

        candidate = f"{current}\n\n{section}".strip() if current else section
        if current and len(candidate) > max_size:
            parts.append(current)
            current = section
        else:
            current = candidate

    if current:
        parts.append(current)

    return parts


def _parse_section_header(content: str) -> Dict[str, str]:
    first_line = content.split("\n", 1)[0].strip()
    match = re.match(r"^#{1,3}\s+((?:\d+(?:\.\d+)*)\.)\s*(.*)$", first_line)
    if not match:
        return {}

    section_label = match.group(1).rstrip(".")
    title_tail = match.group(2).strip()
    chapter = section_label.split(".")[0]
    return {
        "section": section_label,
        "chapter": chapter,
        "chapter_title": title_tail[:200],
    }


def _detect_chunk_type(content: str) -> str:
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    list_lines = sum(1 for line in lines if line.startswith("-") or line.startswith("−"))
    lowered = content.lower()

    if list_lines >= 3 and "соответствии с" in lowered:
        return "reference"
    if list_lines >= 2:
        return "list"
    if any(marker in lowered for marker in ("порядок", "процедура", "включает в себя", "осуществляется")):
        return "procedure"
    if any(marker in lowered for marker in ("представляет собой", "является", "устанавливает")):
        return "definition"
    return "rule"


def enrich_chunk_metadata(chunk: Dict, document_id: str = "") -> Dict:
    content = chunk.get("content", "")
    header = _parse_section_header(content)
    section = chunk.get("section") or header.get("section", "")
    chapter = chunk.get("chapter") or header.get("chapter", "")

    if section and (not chunk.get("id") or chunk["id"].startswith(("chunk_", "section_"))):
        chunk["id"] = f"p_{section.replace('.', '_')}"

    if section:
        chunk["section"] = section
    if chapter:
        chunk["chapter"] = chapter
    if header.get("chapter_title") and not chunk.get("title"):
        chunk["title"] = f"{section}. {header['chapter_title']}" if section else header["chapter_title"]

    first_line = content.split("\n", 1)[0].strip()
    if not chunk.get("title"):
        chunk["title"] = re.sub(r"^#{1,3}\s+", "", first_line)[:120] or "Фрагмент"
    if not chunk.get("abstract"):
        chunk["abstract"] = chunk["title"][:200]

    chunk["chunk_type"] = chunk.get("chunk_type") or _detect_chunk_type(content)
    if document_id:
        chunk["document_id"] = document_id
    chunk["size"] = len(content)
    return chunk


def _same_merge_group(left: Dict, right: Dict) -> bool:
    left_section = left.get("section", "")
    right_section = right.get("section", "")
    if left_section and right_section:
        return left.get("chapter") == right.get("chapter")
    return True


def merge_small_chunks(chunks: List[Dict], min_size: int = MIN_CHUNK_SIZE) -> List[Dict]:
    if not chunks:
        return []

    merged: List[Dict] = []
    buffer = chunks[0].copy()

    for chunk in chunks[1:]:
        can_merge = len(buffer["content"]) < min_size and _same_merge_group(buffer, chunk)
        if can_merge:
            buffer["content"] = f"{buffer['content']}\n\n{chunk['content']}"
            buffer["size"] = len(buffer["content"])
            if chunk.get("section"):
                buffer["section"] = f"{buffer.get('section', '')},{chunk['section']}".strip(",")
        else:
            merged.append(buffer)
            buffer = chunk.copy()

    merged.append(buffer)
    return merged


def rule_based_chunks(text: str, document_id: str = "") -> List[Dict]:
    sections = split_into_sections(text)
    packed = pack_sections(sections, CHUNK_TARGET_SIZE)
    chunks: List[Dict] = []

    for index, content in enumerate(packed):
        chunk = {
            "id": f"section_{index:03d}",
            "title": "",
            "abstract": "",
            "size": len(content),
            "content": content,
        }
        chunks.append(enrich_chunk_metadata(chunk, document_id))

    return chunks


def _extract_message_content(message: dict) -> str:
    content = message.get("content")
    if content:
        return content.strip()
    return ""


def _format_chunk_summary(chunks: List[Dict]) -> str:
    if not chunks:
        return "  (чанков нет)"

    lines = [f"  Всего чанков: {len(chunks)}"]
    for index, chunk in enumerate(chunks, start=1):
        chunk_id = chunk.get("id", f"chunk_{index}")
        title = (chunk.get("title") or chunk.get("abstract") or "")[:100]
        size = chunk.get("size", len(chunk.get("content", "")))
        lines.append(f"  {index}. {chunk_id} | {size} симв. | {title}")
    return "\n".join(lines)


def _append_llm_log(
    *,
    source_name: str,
    document_id: str,
    part_index: int,
    parts_total: int,
    input_chars: int,
    model: str,
    finish_reason: Optional[str],
    raw_content: str,
    chunks: Optional[List[Dict]] = None,
    status: str,
    details: str = "",
) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    chunk_summary = _format_chunk_summary(chunks or [])

    block = f"""
{'=' * 80}
[{timestamp}] LLM-ответ | {status}
Документ: {source_name or '—'}
ID документа: {document_id or '—'}
Часть: {part_index}/{parts_total}
Модель: {model}
Размер входного текста: {input_chars} символов
Причина завершения: {finish_reason or '—'}
{details}

--- Сводка чанков ---
{chunk_summary}

--- Сырой ответ LLM ---
{raw_content or '(пусто)'}
{'=' * 80}
"""
    LLM_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LLM_LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(block.strip() + "\n\n")


def _parse_json_response(raw: str) -> dict:
    raw = raw.strip()
    if not raw:
        raise ValueError("Пустой ответ модели")

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        return json.loads(fenced.group(1))

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        return json.loads(raw[start : end + 1])

    raise ValueError("Ответ модели не содержит JSON")


def llm_chunking_request(
    text: str,
    api_key: str,
    *,
    source_name: str = "",
    document_id: str = "",
    part_index: int = 1,
    parts_total: int = 1,
) -> List[Dict]:
    prompt = CHUNKING_PROMPT.format(text=text)

    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1500,
        "temperature": 0.2,
    }

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Help_System_KnGraph",
            "X-Title": "Help System KnGraph Chunk Extractor",
        },
        json=body,
        timeout=300,
    )

    if not response.ok:
        error_text = response.text[:2000]
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=None,
            raw_content=error_text,
            status="ОШИБКА HTTP",
            details=f"HTTP {response.status_code}",
        )
        raise RuntimeError(f"OpenRouter HTTP {response.status_code}: {response.text[:500]}")

    data = response.json()
    if data.get("error"):
        error_text = json.dumps(data["error"], ensure_ascii=False, indent=2)
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=None,
            raw_content=error_text,
            status="ОШИБКА API",
            details="OpenRouter вернул error в теле ответа",
        )
        raise RuntimeError(f"OpenRouter error: {data['error']}")

    choices = data.get("choices") or []
    if not choices:
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=None,
            raw_content=json.dumps(data, ensure_ascii=False, indent=2)[:5000],
            status="ОШИБКА",
            details="OpenRouter вернул пустой choices",
        )
        raise RuntimeError(f"OpenRouter вернул пустой choices: {data}")

    choice = choices[0]
    message = choice.get("message") or {}
    raw_content = _extract_message_content(message)
    finish_reason = choice.get("finish_reason")

    if not raw_content:
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=finish_reason,
            raw_content=json.dumps(message, ensure_ascii=False, indent=2),
            status="ОШИБКА",
            details=f"Пустой content (finish_reason={finish_reason})",
        )
        raise RuntimeError(
            f"Пустой content в ответе модели (finish_reason={finish_reason}). "
            f"Ключи message: {list(message.keys())}"
        )

    try:
        payload = _parse_json_response(raw_content)
        chunks = payload.get("chunks") or payload.get("chunks_1") or []
        if not chunks:
            raise ValueError("JSON ответа не содержит массива chunks")

        normalized = _normalize_chunk_list(chunks, document_id)
        combined_len = sum(len(chunk.get("content", "")) for chunk in normalized)
        coverage_ratio = combined_len / max(len(text), 1)
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=finish_reason,
            raw_content=raw_content,
            chunks=normalized,
            status="УСПЕХ",
            details=(
                f"Покрытие текста части: {combined_len}/{len(text)} символов "
                f"({coverage_ratio:.1%})"
            ),
        )
        return normalized
    except Exception as error:
        _append_llm_log(
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
            input_chars=len(text),
            model=MODEL,
            finish_reason=finish_reason,
            raw_content=raw_content,
            status="ОШИБКА ПАРСИНГА",
            details=str(error),
        )
        raise


def _normalize_chunk_list(chunks: List[Dict], document_id: str = "") -> List[Dict]:
    normalized: List[Dict] = []
    for index, chunk in enumerate(chunks):
        content = chunk.get("content", "")
        item = {
            "id": chunk.get("id") or f"chunk_{index:03d}",
            "title": chunk.get("title") or "",
            "abstract": chunk.get("abstract") or "",
            "size": len(content),
            "content": content,
        }
        normalized.append(enrich_chunk_metadata(item, document_id))
    return normalized


def validate_coverage(source_text: str, chunks: List[Dict], min_ratio: float = 0.85) -> bool:
    if not chunks:
        return False
    total = sum(len(chunk.get("content", "")) for chunk in chunks)
    return total / max(len(source_text), 1) >= min_ratio


def process_text_part(
    text_part: str,
    api_key: str,
    document_id: str = "",
    *,
    source_name: str = "",
    part_index: int = 1,
    parts_total: int = 1,
) -> List[Dict]:
    try:
        chunks = llm_chunking_request(
            text_part,
            api_key,
            source_name=source_name,
            document_id=document_id,
            part_index=part_index,
            parts_total=parts_total,
        )
        if chunks and validate_coverage(text_part, chunks):
            return chunks
        if chunks:
            combined_len = sum(len(chunk.get("content", "")) for chunk in chunks)
            message = (
                f"LLM-чанки не покрывают текст части "
                f"({combined_len}/{len(text_part)} символов), используется rule-based fallback"
            )
            print(f"  Предупреждение: {message}")
            _append_llm_log(
                source_name=source_name,
                document_id=document_id,
                part_index=part_index,
                parts_total=parts_total,
                input_chars=len(text_part),
                model=MODEL,
                finish_reason=None,
                raw_content="",
                chunks=chunks,
                status="FALLBACK",
                details=message,
            )
        else:
            print("  Предупреждение: LLM вернул пустой список чанков, используется rule-based fallback")
    except Exception as error:
        print(f"  Ошибка LLM для части текста: {error}")

    fallback_chunks = rule_based_chunks(text_part, document_id)
    _append_llm_log(
        source_name=source_name,
        document_id=document_id,
        part_index=part_index,
        parts_total=parts_total,
        input_chars=len(text_part),
        model=MODEL,
        finish_reason=None,
        raw_content="",
        chunks=fallback_chunks,
        status="RULE-BASED FALLBACK",
        details="Использованы чанки, сформированные без LLM",
    )
    return fallback_chunks


def process_document_text(
    text: str,
    api_key: str,
    document_id: str = "",
    *,
    source_name: str = "",
) -> List[Dict]:
    prepared = prepare_text(text)
    indexable = extract_indexable_body(prepared)
    sections = split_into_sections(indexable)
    parts = pack_sections(sections, MAX_PART_SIZE)

    if not parts:
        return []

    all_chunks: List[Dict] = []
    parts_total = len(parts)
    for part_index, part in enumerate(tqdm(parts, desc="Обработка частей документа"), start=1):
        all_chunks.extend(
            process_text_part(
                part,
                api_key,
                document_id,
                source_name=source_name,
                part_index=part_index,
                parts_total=parts_total,
            )
        )

    all_chunks = merge_small_chunks(all_chunks)

    if not validate_coverage(indexable, all_chunks):
        coverage = sum(len(chunk.get("content", "")) for chunk in all_chunks)
        print(
            f"  Предупреждение: итоговые чанки покрывают {coverage}/{len(indexable)} символов "
            f"({coverage / len(indexable):.1%})"
        )

    for index, chunk in enumerate(all_chunks):
        chunk["serial"] = index
        enrich_chunk_metadata(chunk, document_id)

    return all_chunks


def save_document_chunks(chunks: List[Dict], source_name: str, document_id: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / f"{Path(source_name).stem}.json"

    payload = {
        "source": source_name,
        "document_id": document_id,
        "chunks": chunks,
    }

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)

    return output_path


def process_markdown(md_path: Path, api_key: str) -> Path:
    print(f"Обработка файла: {md_path.name}")
    text = read_markdown(md_path)
    print(f"Извлечено {len(text)} символов")

    document_id = extract_document_id(text, md_path.name)
    if LLM_LOG_PATH.exists():
        LLM_LOG_PATH.write_text("", encoding="utf-8")
    _append_llm_log(
        source_name=md_path.name,
        document_id=document_id,
        part_index=0,
        parts_total=0,
        input_chars=len(text),
        model=MODEL,
        finish_reason=None,
        raw_content="",
        status="СТАРТ",
        details=f"Начата обработка документа, извлечено {len(text)} символов",
    )
    chunks = process_document_text(text, api_key, document_id, source_name=md_path.name)
    print(f"Сгенерировано {len(chunks)} чанков")

    output_path = save_document_chunks(chunks, md_path.name, document_id)
    _append_llm_log(
        source_name=md_path.name,
        document_id=document_id,
        part_index=0,
        parts_total=0,
        input_chars=len(text),
        model=MODEL,
        finish_reason=None,
        raw_content="",
        chunks=chunks,
        status="ЗАВЕРШЕНО",
        details=f"Сохранено {len(chunks)} чанков в {output_path.name}",
    )
    print(f"Чанки сохранены в {output_path}")
    print(f"Лог LLM: {LLM_LOG_PATH}")
    return output_path


def process_all_markdown(input_dir: Optional[Path] = None, api_key: Optional[str] = None) -> List[Path]:
    input_dir = input_dir or INPUT_DIR
    api_key = api_key or get_api_key()

    md_files = sorted(input_dir.glob("*.md"))
    if not md_files:
        raise FileNotFoundError(f"В каталоге {input_dir} не найдено .md файлов")

    saved_paths: List[Path] = []
    for md_path in md_files:
        saved_paths.append(process_markdown(md_path, api_key))

    return saved_paths


if __name__ == "__main__":
    process_all_markdown()
