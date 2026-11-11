import argparse
import json
import re
import unicodedata
from html.parser import HTMLParser
from pathlib import Path

from charset_normalizer import from_path

FIELDS = ["wiki_id", "freebase_id", "title", "author", "date", "genres", "summary"]


def detect_encoding(path: Path) -> str:
    best = from_path(path).best()
    if best is None:
        raise RuntimeError("Не вдалося визначити кодування файлу")
    return best.encoding


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)


_MARKUP = re.compile(r"<[A-Za-z/!][^>]*>|&[#A-Za-z0-9]+;")


def strip_html(text: str) -> str:
    if not _MARKUP.search(text):
        return text
    parser = _TextExtractor()
    parser.feed(text)
    parser.close()
    return " ".join(parser.parts)


def clean_text(text: str) -> str:
    text = strip_html(text)
    text = unicodedata.normalize("NFC", text)
    # видаляємо керівні та невидимі символи форматування (BOM, нульова ширина)
    text = "".join(
        ch for ch in text
        if ch.isspace() or unicodedata.category(ch) not in ("Cc", "Cf")
    )
    return " ".join(text.split())


def parse_genres(raw: str) -> list:
    raw = raw.strip()
    if not raw:
        return []
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        return []
    return [clean_text(v) for v in obj.values()] if isinstance(obj, dict) else []


def run(src: Path, dst: Path, stats_path: Path) -> dict:
    enc = detect_encoding(src)
    stats = {
        "source": str(src),
        "detected_encoding": enc,
        "converted_to_utf8": enc.lower().replace("_", "-") not in ("utf-8", "ascii"),
        "lines_read": 0,
        "malformed_lines": 0,
        "records_written": 0,
    }
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, encoding=enc, newline="") as fin, open(dst, "w", encoding="utf-8", newline="\n") as fout:
        for line in fin:
            line = line.rstrip("\r\n")
            if not line:
                continue
            stats["lines_read"] += 1
            cols = line.split("\t")
            if len(cols) != len(FIELDS):
                stats["malformed_lines"] += 1
                continue
            rec = {k: clean_text(v) for k, v in zip(FIELDS, cols) if k != "genres"}
            rec["genres"] = parse_genres(cols[FIELDS.index("genres")])
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["records_written"] += 1
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Етап 1: кодування, очищення, запис у JSONL")
    ap.add_argument("--src", type=Path, default=Path("data/raw/booksummaries.txt"))
    ap.add_argument("--dst", type=Path, default=Path("data/interim/cleaned.jsonl"))
    ap.add_argument("--stats", type=Path, default=Path("data/interim/stage1_stats.json"))
    a = ap.parse_args()
    print(json.dumps(run(a.src, a.dst, a.stats), ensure_ascii=False, indent=2))
