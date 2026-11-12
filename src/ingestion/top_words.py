import argparse
import json
import re
from collections import Counter
from pathlib import Path

from llama_index.core.utils import globals_helper

WORD = re.compile(r"[a-z]+")


def run(src: Path, out: Path, top: int) -> dict:
    stop = set(globals_helper.stopwords)  # англійські стоп-слова, що постачаються з LlamaIndex
    all_words, content_words = Counter(), Counter()
    with open(src, encoding="utf-8") as f:
        for line in f: 
            words = WORD.findall(json.loads(line)["summary"].lower())
            all_words.update(words)
            content_words.update(w for w in words if w not in stop)
    result = {
        "source": str(src),
        "total_words": sum(all_words.values()),
        "unique_words": len(all_words),
        "stopwords_count": len(stop),
        "top_with_stopwords": all_words.most_common(top),
        "top_without_stopwords": content_words.most_common(top),
    }
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Топ найчастотніших слів корпусу")
    ap.add_argument("--src", type=Path, default=Path("data/processed/documents.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("data/processed/top_words.json"))
    ap.add_argument("--top", type=int, default=20)
    a = ap.parse_args()
    r = run(a.src, a.out, a.top)
    print(r["total_words"], r["unique_words"])
    print(r["top_with_stopwords"])
    print(r["top_without_stopwords"])
