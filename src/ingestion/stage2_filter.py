import argparse
import json
import random
from pathlib import Path

REQUIRED = ["wiki_id", "freebase_id", "title", "author", "date", "genres", "summary"]


def run(src: Path, dst: Path, stats_path: Path, min_len: int, max_docs: int, seed: int) -> dict:
    stats = {
        "records_read": 0,
        "after_fields_filled": 0,
        "after_min_summary_len": 0,
        "after_unique_id": 0,
        "min_summary_chars": min_len,
        "max_docs": max_docs,
        "seed": seed,
    }
    kept, seen = [], set()
    with open(src, encoding="utf-8") as fin:
        for line in fin:
            rec = json.loads(line)
            stats["records_read"] += 1
            # 1. усі поля заповнені, список жанрів не порожній
            if not all(rec.get(k) for k in REQUIRED):
                continue
            stats["after_fields_filled"] += 1
            # 2. мінімальна довжина опису
            if len(rec["summary"]) < min_len:
                continue
            stats["after_min_summary_len"] += 1
            # 3. унікальний ідентифікатор статті
            if rec["wiki_id"] in seen:
                continue
            seen.add(rec["wiki_id"])
            stats["after_unique_id"] += 1
            kept.append(rec)
    # 4. верхня межа обсягу: відтворювана випадкова вибірка, початковий порядок зберігається
    if len(kept) > max_docs:
        idx = sorted(random.Random(seed).sample(range(len(kept)), max_docs))
        kept = [kept[i] for i in idx]
    # 5. ключ doc_id = doc_{wiki_id}_{наш послідовний номер у фінальному корпусі}
    kept = [{"doc_id": f"doc_{rec['wiki_id']}_{i}", **rec} for i, rec in enumerate(kept, start=1)]
    stats["final_documents"] = len(kept)
    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as fout:
        for rec in kept:
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Етап 2: фільтрація записів")
    ap.add_argument("--src", type=Path, default=Path("data/interim/cleaned.jsonl"))
    ap.add_argument("--dst", type=Path, default=Path("data/processed/documents.jsonl"))
    ap.add_argument("--stats", type=Path, default=Path("data/processed/stage2_stats.json"))
    ap.add_argument("--min-len", type=int, default=100)
    ap.add_argument("--max-docs", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    print(json.dumps(run(a.src, a.dst, a.stats, a.min_len, a.max_docs, a.seed), ensure_ascii=False, indent=2))
