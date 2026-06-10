"""
Milestone 4 — Embedding, vector store, and retrieval
University Career Assistant (RAG)

Pipeline stage (see planning.md → Architecture):

    Chunking            ->  Embedding + Vector Store  ->  Retrieval
    (data/chunks.json)      (all-MiniLM-L6-v2,             (semantic search,
                             ChromaDB, cosine)              top-k = 5)

This module:
  - embed_and_store(): loads the chunks produced by ingest.py, embeds each one
    with SentenceTransformer("all-MiniLM-L6-v2"), and stores them in a
    persistent ChromaDB collection with `source` + `chunk_index` metadata
    (needed for source attribution in Milestone 5).
  - retrieve(query, k=5): embeds the query with the SAME model and returns the
    top-k most similar chunks, each with its text, source, chunk_index, and a
    cosine distance score (0 = identical, 1 = unrelated, 2 = opposite).

Run:
    python rag.py build              # (re)build the vector store from chunks
    python rag.py query "your question here"
    python rag.py eval               # run the planning.md eval questions
    python rag.py                    # build, then run eval (one-shot check)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — keep aligned with planning.md → Retrieval Approach
# ---------------------------------------------------------------------------

EMBED_MODEL = "all-MiniLM-L6-v2"   # local, no API key, no rate limits
CHUNKS_FILE = Path("data/chunks.json")
CHROMA_DIR = Path("chroma_db")     # gitignored — local persistent store
COLLECTION_NAME = "career_chunks"
DEFAULT_TOP_K = 5                  # planning.md: Top-K = 5

# Evaluation questions from planning.md → Evaluation Plan.
EVAL_QUESTIONS = [
    "What are some common skills in Data Science student resumes?",
    "For a job interview, what are some tips for my thank you note?",
    "I want to network but don't know where to start. What are some USD-specific resources?",
    "Why should I use AI in my job preparation process?",
    "How do I find salary and job outlook information?",
]


# ---------------------------------------------------------------------------
# Lazy singletons — the model and the DB client are expensive to construct,
# so we build each one once and reuse it across calls.
# ---------------------------------------------------------------------------

_model = None
_collection = None


def get_model():
    """Load the embedding model once (downloads/caches on first use)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_collection():
    """
    Open (or create) the persistent ChromaDB collection.

    - PersistentClient writes the index to CHROMA_DIR so embeddings survive
      between runs (no need to re-embed every time).
    - hnsw:space="cosine" tells ChromaDB to rank by COSINE distance instead of
      its default squared-L2. Cosine fits normalized sentence embeddings and
      gives an interpretable 0–2 scale, so the "distance < 0.5" check in our
      verification plan is meaningful.
    """
    global _collection
    if _collection is None:
        import chromadb
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _reset_collection():
    """Drop the collection so a rebuild reflects exactly the current chunks."""
    global _collection
    import chromadb
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass  # didn't exist yet — fine
    _collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


# ---------------------------------------------------------------------------
# Embedding + storage
# ---------------------------------------------------------------------------

def embed_and_store(chunks_file: Path = CHUNKS_FILE) -> int:
    """
    Embed every chunk and (re)load them into ChromaDB with source metadata.

    Returns the number of chunks stored.
    """
    if not chunks_file.exists():
        raise FileNotFoundError(
            f"{chunks_file} not found — run `python ingest.py` first.")

    chunks = json.loads(chunks_file.read_text(encoding="utf-8"))
    if not chunks:
        raise ValueError("No chunks to embed.")

    print(f"Loading {len(chunks)} chunks from {chunks_file}")
    model = get_model()

    texts = [c["text"] for c in chunks]
    # normalize_embeddings=True -> unit vectors, which pairs cleanly with the
    # cosine space configured on the collection.
    print(f"Embedding with '{EMBED_MODEL}' ...")
    embeddings = model.encode(
        texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True
    ).tolist()

    # A stable, unique id per chunk lets us upsert idempotently.
    ids = [f"{c['source']}::{c['chunk_index']}" for c in chunks]
    metadatas = [
        {"source": c["source"], "chunk_index": c["chunk_index"]}
        for c in chunks
    ]

    print("Storing in ChromaDB (rebuilding collection) ...")
    collection = _reset_collection()
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    count = collection.count()
    print(f"Stored {count} chunks in collection '{COLLECTION_NAME}' "
          f"-> {CHROMA_DIR}/")
    return count


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def retrieve(query: str, k: int = DEFAULT_TOP_K) -> list[dict]:
    """
    Return the top-k chunks most semantically similar to `query`.

    Each result is a dict:
        {"text": str, "source": str, "chunk_index": int, "distance": float}
    where lower distance = more relevant (cosine: 0 identical .. 2 opposite).
    """
    model = get_model()
    q_emb = model.encode([query], normalize_embeddings=True).tolist()

    collection = get_collection()
    res = collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    # ChromaDB returns parallel lists wrapped one level deep (per query).
    results = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        results.append({
            "text": text,
            "source": meta["source"],
            "chunk_index": meta["chunk_index"],
            "distance": dist,
        })
    return results


# ---------------------------------------------------------------------------
# Generation (Milestone 5) — grounded answers via Groq
# ---------------------------------------------------------------------------

GROQ_MODEL = "llama-3.3-70b-versatile"
RESOURCES_FILE = Path("data/resources.json")

# The decline message the model must use when the context can't answer. We keep
# it as a constant so the UI and tests can recognize an out-of-scope response.
DECLINE_MESSAGE = ("I don't have information on that in the USD career resources "
                   "I have access to.")

SYSTEM_PROMPT = f"""You are the University of San Diego (USD) Career Assistant.
You answer students' career questions using ONLY the numbered context excerpts
provided in the user message. Those excerpts are drawn from official USD
career-center documents.

Rules:
- Use ONLY information found in the provided context. Do not use outside or
  prior knowledge, and do not make assumptions beyond what the excerpts state.
- If the context does not contain enough information to answer the question,
  reply with EXACTLY this sentence and nothing else:
  "{DECLINE_MESSAGE}"
- Be concise, specific, and practical. You may synthesize across excerpts.
- Never fabricate sources, statistics, URLs, names, or quotes.
- Do not list or cite sources yourself — the system attaches sources separately.
"""


def _format_context(chunks: list[dict]) -> str:
    """Render retrieved chunks into a numbered context block for the prompt."""
    blocks = []
    for i, c in enumerate(chunks, 1):
        blocks.append(f"[{i}] (source: {c['source']})\n{c['text']}")
    return "\n\n".join(blocks)


def _unique_sources(chunks: list[dict]) -> list[str]:
    """Source document names, de-duplicated, in order of first appearance."""
    seen, ordered = set(), []
    for c in chunks:
        if c["source"] not in seen:
            seen.add(c["source"])
            ordered.append(c["source"])
    return ordered


def _relevant_resources(query: str) -> list[dict]:
    """
    Return website links (from data/resources.json) whose topic keywords appear
    in the query. These are surfaced as recommendations, not embedded/retrieved.
    """
    if not RESOURCES_FILE.exists():
        return []
    resources = json.loads(RESOURCES_FILE.read_text(encoding="utf-8"))
    q = query.lower()
    matches = []
    for r in resources:
        if any(kw.lower() in q for kw in r.get("keywords", [])):
            matches.append({"name": r["name"], "url": r["url"],
                            "description": r["description"]})
    return matches


def ask(query: str, k: int = DEFAULT_TOP_K) -> dict:
    """
    Answer `query` grounded in the top-k retrieved chunks.

    Returns:
        {
          "answer":    str,          # the model's grounded answer (or decline)
          "sources":   list[str],    # source docs, attached programmatically
          "resources": list[dict],   # relevant website links (name/url/desc)
          "chunks":    list[dict],   # the retrieved chunks (for transparency)
        }
    """
    import os
    from dotenv import load_dotenv
    from groq import Groq

    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Add it to your .env file "
            "(get a free key at https://console.groq.com).")

    chunks = retrieve(query, k=k)
    context = _format_context(chunks)

    client = Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        temperature=0,  # grounded Q&A — we want faithful, not creative, output
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",
             "content": f"Context excerpts:\n\n{context}\n\nQuestion: {query}"},
        ],
    )
    answer = completion.choices[0].message.content.strip()

    # Source attribution is computed from chunk metadata, NOT left to the model.
    # If the model declined, we don't attach sources (nothing was used).
    declined = answer.strip().rstrip(".") == DECLINE_MESSAGE.rstrip(".")
    sources = [] if declined else _unique_sources(chunks)

    return {
        "answer": answer,
        "sources": sources,
        "resources": _relevant_resources(query),
        "chunks": chunks,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _print_results(query: str, results: list[dict], preview_chars: int = 220) -> None:
    print(f"\nQuery: {query}")
    if not results:
        print("  (no results — is the store built?)")
        return
    for rank, r in enumerate(results, 1):
        preview = r["text"].replace("\n", " ")
        if len(preview) > preview_chars:
            preview = preview[:preview_chars] + " ..."
        flag = "" if r["distance"] < 0.5 else "   <- distance >= 0.5"
        print(f"  {rank}. [{r['distance']:.3f}] {r['source']} #{r['chunk_index']}{flag}")
        print(f"     {preview}")


def run_eval(k: int = DEFAULT_TOP_K) -> None:
    """Run the planning.md eval questions and report retrieval quality."""
    print("=" * 78)
    print(f"Retrieval check — {len(EVAL_QUESTIONS)} questions, top-{k}, "
          f"target: top result distance < 0.5")
    print("=" * 78)
    passed = 0
    for q in EVAL_QUESTIONS:
        results = retrieve(q, k=k)
        _print_results(q, results)
        if results and results[0]["distance"] < 0.5:
            passed += 1
    print("\n" + "=" * 78)
    print(f"{passed}/{len(EVAL_QUESTIONS)} questions had a top result with "
          f"distance < 0.5")


def main() -> int:
    parser = argparse.ArgumentParser(description="Embed chunks and retrieve them.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("build", help="Embed all chunks and (re)build the vector store.")

    q = sub.add_parser("query", help="Retrieve top-k chunks for a query.")
    q.add_argument("text", help="The query string.")
    q.add_argument("-k", type=int, default=DEFAULT_TOP_K)

    e = sub.add_parser("eval", help="Run the planning.md evaluation questions.")
    e.add_argument("-k", type=int, default=DEFAULT_TOP_K)

    a = sub.add_parser("ask", help="Ask a grounded question (calls Groq).")
    a.add_argument("text", help="The question to ask.")
    a.add_argument("-k", type=int, default=DEFAULT_TOP_K)

    args = parser.parse_args()

    if args.command == "build":
        embed_and_store()
    elif args.command == "query":
        _print_results(args.text, retrieve(args.text, k=args.k))
    elif args.command == "eval":
        run_eval(k=args.k)
    elif args.command == "ask":
        result = ask(args.text, k=args.k)
        print(f"\nQ: {args.text}\n")
        print(result["answer"])
        if result["sources"]:
            print("\nSources:")
            for s in result["sources"]:
                print(f"  - {s}")
        if result["resources"]:
            print("\nYou may also find these helpful:")
            for r in result["resources"]:
                print(f"  - {r['name']}: {r['url']}")
    else:
        # No subcommand: build, then run the eval as a one-shot sanity check.
        embed_and_store()
        print()
        run_eval()

    return 0


if __name__ == "__main__":
    sys.exit(main())
