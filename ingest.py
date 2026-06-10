"""
Milestone 3 — Document ingestion and chunking
University Career Assistant (RAG)

Pipeline stage (see planning.md → Architecture):

    Document Ingestion  ->  Cleaning  ->  Chunking
    (local PDFs)            (strip          (200 tokens,
                             boilerplate)    100 overlap)

This script:
  1. Loads every local PDF from "USD sources/".
  2. Saves the RAW extracted text to a consistent format (data/raw/<source>.txt)
     *before* any cleaning, so the original is always recoverable.
  3. Cleans the text (strips HTML, boilerplate, collapses whitespace) and saves
     it to data/cleaned/<source>.txt.
  4. Chunks the cleaned text into 200-token windows with 100-token overlap,
     counting tokens with the *same* tokenizer the embedding model uses
     (all-MiniLM-L6-v2), and writes the chunks to data/chunks.json.

The two website sources (RoadTrip Nation, CareerShift) are NOT chunked. They are
interactive JavaScript apps, so there is no useful prose to embed — instead we
register them in data/resources.json as recommendable links, to be surfaced by
the generation stage (Milestone 5) when a user asks a related question.

Output schema (one entry per chunk), ready for Milestone 4 embedding:
    {"text": str, "source": str, "chunk_index": int}

Run:
    python ingest.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration — keep these aligned with planning.md / README.md
# ---------------------------------------------------------------------------

CHUNK_SIZE = 200      # tokens per chunk  (planning.md: "fixed chunk size at 200 tokens")
CHUNK_OVERLAP = 100   # tokens of overlap (planning.md: "100 tokens")

# The embedding model from the Architecture diagram. We count tokens with this
# exact tokenizer so a "200-token chunk" means 200 tokens *as the embedder sees
# them* — not a rough word estimate.
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

SOURCES_DIR = Path("USD sources")   # local PDF corpus
DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
CLEANED_DIR = DATA_DIR / "cleaned"
CHUNKS_FILE = DATA_DIR / "chunks.json"
RESOURCES_FILE = DATA_DIR / "resources.json"

# Website sources (planning.md / README.md Documents table). These are
# interactive JS apps with no useful prose to chunk, so we do NOT embed them.
# Instead we register them as recommendable links. The `keywords` are used by
# the generation stage to decide when a user's question is "related" and the
# link is worth surfacing.
URL_RESOURCES = [
    {
        "name": "RoadTrip Nation",
        "url": "https://roadtripnation.com/edu/sandiego",
        "description": ("Watch stories and informational interviews from real "
                        "people across many fields to get advice, explore "
                        "careers, and research salary and job-outlook info."),
        "keywords": ["explore careers", "career exploration", "informational interview",
                     "videos", "stories", "advice", "salary", "job outlook",
                     "career paths", "industries", "what career"],
    },
    {
        "name": "CareerShift",
        "url": "https://www.careershift.com/?sc=Sandiego",
        "description": ("Search job listings aggregated from multiple job boards, "
                        "build target-company lists, and find key contact "
                        "information for your job search."),
        "keywords": ["job search", "job listings", "job boards", "find a job",
                     "job postings", "company list", "target companies",
                     "contacts", "apply", "openings"],
    },
]


@dataclass
class Document:
    """A single source document after raw extraction."""
    source: str       # human-readable source name (used in citations later)
    raw_text: str     # text exactly as extracted, before cleaning


# ---------------------------------------------------------------------------
# Loading — local PDFs
# ---------------------------------------------------------------------------

def load_pdf(path: Path) -> str:
    """
    Extract raw text from a PDF, one page after another.

    We use PyMuPDF (fitz) rather than pdfplumber: several of the career-guide
    PDFs use custom glyph spacing that pdfplumber mis-orders into scrambled
    text ("insgtr ongleyn" instead of "I strongly"). PyMuPDF reads the content
    stream in the correct order and extracts these cleanly.
    """
    import fitz  # PyMuPDF

    pages = []
    with fitz.open(path) as pdf:
        for page in pdf:
            pages.append(page.get_text())
    return "\n".join(pages)


def load_local_documents(sources_dir: Path) -> list[Document]:
    """Load every PDF in `sources_dir` from disk."""
    docs: list[Document] = []
    pdf_paths = sorted(sources_dir.glob("*.pdf"))
    if not pdf_paths:
        print(f"  ! No PDFs found in {sources_dir}/")
    for path in pdf_paths:
        try:
            raw = load_pdf(path)
        except Exception as exc:  # one bad PDF shouldn't kill the run
            print(f"  ! Failed to read {path.name}: {exc}")
            continue
        docs.append(Document(source=path.stem, raw_text=raw))
        print(f"  + {path.name}  ({len(raw):,} chars)")
    return docs


# ---------------------------------------------------------------------------
# Cleaning
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    Normalize extracted text:
      - strip any leftover HTML tags
      - join words broken across a line by a hyphen ("inter-\\nview" -> "interview")
      - collapse runs of spaces/tabs
      - collapse 3+ blank lines down to a single blank line
      - drop empty / whitespace-only lines' surrounding noise
    """
    # Remove stray HTML tags (mostly relevant for scraped pages).
    text = re.sub(r"<[^>]+>", " ", text)

    # Rejoin hyphenated line breaks produced by PDF extraction.
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)

    # Normalize line endings.
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Collapse spaces/tabs (but keep newlines).
    text = re.sub(r"[ \t]+", " ", text)

    # Trim trailing spaces on each line.
    text = "\n".join(line.strip() for line in text.split("\n"))

    # Collapse 3+ consecutive newlines into a paragraph break.
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Chunking — 200 tokens, 100-token overlap, MiniLM tokenizer
# ---------------------------------------------------------------------------

def _load_tokenizer():
    """Load the embedding model's tokenizer (downloads/caches on first use)."""
    from transformers import AutoTokenizer
    # use_fast=True gives us offset mapping, which lets us slice the ORIGINAL
    # text by character — so chunks have no "##" sub-word artifacts.
    return AutoTokenizer.from_pretrained(EMBED_MODEL, use_fast=True)


def chunk_text(
    text: str,
    source: str,
    tokenizer,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[dict]:
    """
    Split `text` into overlapping token windows.

    Tokens are counted with the embedding model's tokenizer. Each window spans
    `chunk_size` tokens and the next window starts `chunk_size - overlap` tokens
    later. We slice the original string using the tokenizer's offset mapping so
    each chunk is clean, human-readable text.

    Returns a list of {"text", "source", "chunk_index"} dicts.
    """
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()
    if not text:
        return []

    enc = tokenizer(
        text,
        add_special_tokens=False,
        return_offsets_mapping=True,
        truncation=False,
    )
    offsets = enc["offset_mapping"]
    n_tokens = len(offsets)
    step = chunk_size - overlap

    chunks: list[dict] = []
    start = 0
    while start < n_tokens:
        window = offsets[start:start + chunk_size]
        start_char = window[0][0]
        end_char = window[-1][1]
        chunk_str = text[start_char:end_char].strip()
        if chunk_str:
            chunks.append({
                "text": chunk_str,
                "source": source,
                "chunk_index": len(chunks),
            })
        if start + chunk_size >= n_tokens:
            break
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Persistence helpers
# ---------------------------------------------------------------------------

def _safe_filename(source: str) -> str:
    """Turn a source name into a safe .txt filename stem."""
    return re.sub(r"[^A-Za-z0-9._-]+", "_", source).strip("_")


def save_text(directory: Path, source: str, text: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / f"{_safe_filename(source)}.txt").write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def load_documents(sources_dir: Path) -> list[Document]:
    """Load all PDF documents from disk."""
    print(f"Loading local PDFs from '{sources_dir}/' ...")
    return load_local_documents(sources_dir)


def write_resources_registry() -> None:
    """Persist the website links (not chunked) for the generation stage to surface."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESOURCES_FILE.write_text(
        json.dumps(URL_RESOURCES, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nRegistered {len(URL_RESOURCES)} website resources (not chunked) "
          f"-> {RESOURCES_FILE}")
    for r in URL_RESOURCES:
        print(f"  • {r['name']}: {r['url']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest and chunk career documents.")
    parser.add_argument("--sources-dir", type=Path, default=SOURCES_DIR,
                        help="Folder containing source PDFs.")
    parser.add_argument("--chunk-size", type=int, default=CHUNK_SIZE)
    parser.add_argument("--overlap", type=int, default=CHUNK_OVERLAP)
    args = parser.parse_args()

    # --- Stage 1: load raw documents -------------------------------------
    documents = load_documents(args.sources_dir)
    if not documents:
        print("\nNo documents loaded — nothing to do.")
        return 1

    # --- Stage 2: save raw text BEFORE cleaning --------------------------
    print(f"\nSaving raw text to '{RAW_DIR}/' (before cleaning) ...")
    for doc in documents:
        save_text(RAW_DIR, doc.source, doc.raw_text)

    # --- Stage 3: clean + save -------------------------------------------
    print(f"Cleaning text and saving to '{CLEANED_DIR}/' ...")
    cleaned = {}
    for doc in documents:
        cleaned[doc.source] = clean_text(doc.raw_text)
        save_text(CLEANED_DIR, doc.source, cleaned[doc.source])

    # --- Stage 4: chunk ---------------------------------------------------
    print(f"\nChunking at {args.chunk_size} tokens / {args.overlap} overlap "
          f"using '{EMBED_MODEL}' tokenizer ...")
    tokenizer = _load_tokenizer()

    all_chunks: list[dict] = []
    for doc in documents:
        doc_chunks = chunk_text(
            cleaned[doc.source], doc.source, tokenizer,
            chunk_size=args.chunk_size, overlap=args.overlap,
        )
        all_chunks.extend(doc_chunks)
        print(f"  {doc.source}: {len(doc_chunks)} chunks")

    # --- Persist chunks ---------------------------------------------------
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHUNKS_FILE.write_text(json.dumps(all_chunks, indent=2, ensure_ascii=False),
                           encoding="utf-8")

    # --- Register website links (not chunked) ----------------------------
    write_resources_registry()

    # --- Summary + verification ------------------------------------------
    print("\n" + "=" * 60)
    print(f"Done. {len(all_chunks)} chunks from {len(documents)} documents "
          f"-> {CHUNKS_FILE}")
    if 50 <= len(all_chunks) <= 2000:
        print("Chunk count is within the expected 50–2,000 range. ✓")
    else:
        print(f"! Chunk count {len(all_chunks)} is OUTSIDE the expected "
              f"50–2,000 range — review chunk size/sources.")

    # Print a few sample chunks to eyeball quality (M3 verification step).
    import random
    sample = random.sample(all_chunks, min(3, len(all_chunks)))
    for c in sample:
        token_count = len(tokenizer(c["text"], add_special_tokens=False)["input_ids"])
        print("\n" + "-" * 60)
        print(f"[{c['source']} #{c['chunk_index']}]  ({token_count} tokens)")
        preview = c["text"] if len(c["text"]) <= 400 else c["text"][:400] + " ..."
        print(preview)

    return 0


if __name__ == "__main__":
    sys.exit(main())
