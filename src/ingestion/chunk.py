import argparse
import json
import statistics
from contextlib import nullcontext
from pathlib import Path

from huggingface_hub import hf_hub_download
from llama_index.core.node_parser import SentenceSplitter
from tokenizers import Tokenizer

MODEL = "BAAI/bge-small-en-v1.5"
MODEL_MAX_TOKENS = 512


def run(src: Path, dst, stats_path: Path, size: int, overlap: int) -> dict:
    """dst=None: лише статистика без запису чанків (для підбору параметрів)."""
    tk = Tokenizer.from_file(hf_hub_download(MODEL, "tokenizer.json"))
    count = lambda t: len(tk.encode(t, add_special_tokens=False).ids)
    splitter = SentenceSplitter(
        chunk_size=size,
        chunk_overlap=overlap,
        tokenizer=lambda t: tk.encode(t, add_special_tokens=False).ids,
    )
    docs = chunks_total = over_size = not_substring = 0
    token_counts = []
    if dst is not None:
        dst.parent.mkdir(parents=True, exist_ok=True)
    with open(src, encoding="utf-8") as fin, \
            (open(dst, "w", encoding="utf-8", newline="\n") if dst is not None else nullcontext()) as fout:
        for line in fin: 
            doc = json.loads(line)
            docs += 1
            for idx, text in enumerate(splitter.split_text(doc["summary"])):
                rec = {
                    "chunk_id": f"{doc['doc_id']}_{idx}",
                    "doc_id": doc["doc_id"],
                    "chunk_index": idx,
                    "title": doc["title"],
                    "author": doc["author"],
                    "date": doc["date"],
                    "genres": doc["genres"],
                    "text": text,
                }
                if fout is not None:
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n = count(text)
                token_counts.append(n)
                chunks_total += 1
                over_size += n > size
    stats = {
        "model": MODEL,
        "chunker": "llama_index.core.node_parser.SentenceSplitter",
        "chunk_size": size,
        "chunk_overlap": overlap,
        "documents": docs,
        "chunks": chunks_total,
        "tokens_per_chunk_mean": round(statistics.mean(token_counts), 1),
        "tokens_per_chunk_min": min(token_counts),
        "tokens_per_chunk_median": statistics.median(token_counts),
        "tokens_per_chunk_max": max(token_counts),
        "chunks_under_50_tokens": sum(n < 50 for n in token_counts),
        "chunks_under_100_tokens": sum(n < 100 for n in token_counts),
        "chunks_under_50_tokens_pct": round(sum(n < 50 for n in token_counts) / chunks_total * 100, 2),
        "chunks_under_100_tokens_pct": round(sum(n < 100 for n in token_counts) / chunks_total * 100, 2),
        "chunks_over_size": over_size,
        "model_max_tokens": MODEL_MAX_TOKENS,
    }
    stats_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Чанкування документів (SentenceSplitter, LlamaIndex)")
    ap.add_argument("--src", type=Path, default=Path("data/processed/documents.jsonl"))
    ap.add_argument("--dst", type=Path, default=Path("data/processed/chunks.jsonl"))
    ap.add_argument("--stats", type=Path, default=Path("data/processed/chunk_stats.json"))
    ap.add_argument("--size", type=int, default=400)
    ap.add_argument("--overlap", type=int, default=80)
    ap.add_argument("--no-chunks", action="store_true", help="не записувати чанки, лише статистика")
    a = ap.parse_args()
    print(json.dumps(run(a.src, None if a.no_chunks else a.dst, a.stats, a.size, a.overlap), ensure_ascii=False, indent=2))
