"""Build and query a local ChromaDB index from Obsidian Markdown notes."""
from __future__ import annotations

import argparse
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

from .knowledge_reader import get_vault_path, read_obsidian_vault
from .obsidian_writer import append_related_concepts, get_sessions_dir

LOGGER = logging.getLogger(__name__)
# Anchored to the repo, not the working directory, so agents and CLIs launched from anywhere
# (Codex, Claude Code, Task Scheduler) share one index. Each machine builds its own: records
# hold absolute note paths, and a SQLite store must not travel through the vault sync.
DEFAULT_DB_PATH = os.environ.get("AGENCY_CHROMA_DB_PATH") or str(Path(__file__).resolve().parents[4] / "chroma_db")
DEFAULT_COLLECTION_NAME = "second_brain_v2"
# Whole-note collection kept only for rollback and `make rag-eval` comparison.
LEGACY_COLLECTION_NAME = "second_brain"
DEFAULT_BATCH_SIZE = 100
DEFAULT_SESSION_STABILITY_SECONDS = 5.0
RELATED_CONCEPTS_HEADER = "### Related Concepts"
# The default embedder (all-MiniLM-L6-v2) truncates input at 256 word-piece tokens. Vault text runs
# ~2 tokens per word (tables, URLs, brand names), so 80 words keeps ~95% of chunks inside the window.
DEFAULT_CHUNK_WORDS = 80
DEFAULT_CHUNK_OVERLAP_WORDS = 15
# Chunks per requested note fetched before collapsing hits to one result per note.
CHUNK_OVERSAMPLE = 5
MAX_CHUNKS_PER_NOTE = 3
_HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$")
_WIKILINK_UNSAFE = re.compile(r"[\[\]|#^]")


class VectorIndexError(RuntimeError):
    """Raised when the vector index cannot be built."""


def _load_chroma_dependencies():
    """Import Chroma lazily so agency-common remains usable without vector dependencies."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
    except ImportError as exc:
        raise VectorIndexError(
            "chromadb is not installed. Install vector dependencies with "
            "`pip install -e ./packages/agency-common[vector]`."
        ) from exc

    return chromadb, embedding_functions


def prepare_chroma_records(documents: list[dict[str, Any]]) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Convert reader output into Chroma ids, documents, and flat metadata."""
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for doc in documents:
        content = str(doc.get("content") or "")
        if not content.strip():
            LOGGER.warning("Skipping empty Markdown note: %s", doc.get("filepath", "<unknown>"))
            continue

        filepath = str(Path(str(doc["filepath"])).expanduser().resolve())
        ids.append(filepath)
        texts.append(content)
        metadatas.append(
            {
                "filename": str(doc.get("filename") or Path(filepath).name),
                "filepath": filepath,
            }
        )

    return ids, texts, metadatas


def split_markdown_sections(content: str) -> list[tuple[str, str]]:
    """Split Markdown into (heading, body) pairs; text before the first heading has heading ''."""
    sections: list[tuple[str, str]] = []
    heading = ""
    lines: list[str] = []
    in_code_block = False

    for line in content.splitlines():
        if line.lstrip().startswith("```"):
            in_code_block = not in_code_block
        match = None if in_code_block else _HEADING_RE.match(line)
        if match:
            if any(existing.strip() for existing in lines):
                sections.append((heading, "\n".join(lines).strip()))
            heading = match.group(1).strip()
            lines = []
        else:
            lines.append(line)

    if any(existing.strip() for existing in lines):
        sections.append((heading, "\n".join(lines).strip()))
    return sections


def chunk_markdown(
    content: str,
    *,
    max_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> list[tuple[str, str]]:
    """Split Markdown into (heading, text) chunks that never cross a heading boundary."""
    if max_words < 1 or not 0 <= overlap_words < max_words:
        raise ValueError("max_words must be at least 1 and overlap_words must be in [0, max_words)")

    step = max_words - overlap_words
    chunks: list[tuple[str, str]] = []
    for heading, body in split_markdown_sections(content):
        words = body.split()
        for start in range(0, max(len(words) - overlap_words, 1), step):
            chunks.append((heading, " ".join(words[start:start + max_words])))
    return chunks


def prepare_chunk_records(
    documents: list[dict[str, Any]],
    *,
    max_words: int = DEFAULT_CHUNK_WORDS,
    overlap_words: int = DEFAULT_CHUNK_OVERLAP_WORDS,
) -> tuple[list[str], list[str], list[dict[str, Any]]]:
    """Convert reader output into heading-scoped chunk records with `filepath::n` ids."""
    ids: list[str] = []
    texts: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for doc in documents:
        content = str(doc.get("content") or "")
        if not content.strip():
            LOGGER.warning("Skipping empty Markdown note: %s", doc.get("filepath", "<unknown>"))
            continue

        filepath = str(Path(str(doc["filepath"])).expanduser().resolve())
        filename = str(doc.get("filename") or Path(filepath).name)
        title = Path(filename).stem
        chunks = chunk_markdown(content, max_words=max_words, overlap_words=overlap_words)
        for index, (heading, text) in enumerate(chunks):
            ids.append(f"{filepath}::{index}")
            # Prefixing the note title and heading lets a chunk match queries about its context.
            texts.append(f"{title} > {heading}\n{text}" if heading else f"{title}\n{text}")
            metadatas.append({"filename": filename, "filepath": filepath, "heading": heading, "chunk": index})

    return ids, texts, metadatas


def _is_sync_conflict(filepath: Any) -> bool:
    """Syncthing conflict copies duplicate a real note and would crowd it out of results."""
    return ".sync-conflict-" in str(filepath or "")


def _is_chunked(collection: Any) -> bool:
    return bool((getattr(collection, "metadata", None) or {}).get("chunked"))


def _missing_collection_errors(chromadb: Any) -> tuple[type[Exception], ...]:
    """Chroma 1.x raises NotFoundError, which is not a ValueError, for a missing collection."""
    not_found = getattr(getattr(chromadb, "errors", None), "NotFoundError", ValueError)
    return (ValueError, not_found)


def _query_unique_notes(collection: Any, query_text: str, n_results: int) -> list[dict[str, Any]]:
    """Query a chunked collection and collapse chunk hits into the best `n_results` notes.

    Each hit keeps the metadata and distance of its best chunk, plus up to
    MAX_CHUNKS_PER_NOTE matching chunk texts in rank order.
    """
    results = collection.query(
        query_texts=[query_text],
        n_results=n_results * CHUNK_OVERSAMPLE,
        include=["documents", "metadatas", "distances"],
    )
    metadatas = (results.get("metadatas") or [[]])[0]
    documents = (results.get("documents") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]

    hits: dict[str, dict[str, Any]] = {}
    for index, metadata in enumerate(metadatas):
        key = str(metadata.get("filepath") or metadata.get("filename") or "")
        if not key:
            continue
        text = str(documents[index]) if index < len(documents) and documents[index] is not None else ""
        hit = hits.get(key)
        if hit is None:
            if len(hits) == n_results:
                continue
            hit = hits[key] = {
                "metadata": metadata,
                "distance": distances[index] if index < len(distances) else None,
                "chunks": [],
            }
        if len(hit["chunks"]) < MAX_CHUNKS_PER_NOTE:
            hit["chunks"].append(text)
    return list(hits.values())


def _section_wikilink(metadata: dict[str, Any]) -> str | None:
    """Wikilink to the note, pointing at the matched heading when there is one."""
    link = _metadata_to_wikilink(metadata)
    heading = _WIKILINK_UNSAFE.sub("", str(metadata.get("heading") or "")).strip()
    if link is None or not heading:
        return link
    return f"{link[:-2]}#{heading}]]"


def _upsert_batches(
    collection: Any,
    *,
    ids: list[str],
    texts: list[str],
    metadatas: list[dict[str, Any]],
    batch_size: int,
) -> int:
    """Upsert prepared records into Chroma in bounded batches."""
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    indexed_count = 0
    for start in range(0, len(ids), batch_size):
        end = start + batch_size
        collection.upsert(
            documents=texts[start:end],
            metadatas=metadatas[start:end],
            ids=ids[start:end],
        )
        indexed_count += len(ids[start:end])

    return indexed_count


def build_vector_database(
    *,
    vault_path: Path | None = None,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    batch_size: int = DEFAULT_BATCH_SIZE,
    chunked: bool = True,
) -> int:
    """Read the Obsidian vault and embed Markdown notes into a persistent ChromaDB collection.

    With `chunked` (the default), notes are split at headings into embedder-sized chunks. The
    collection is updated in place, never dropped, so the session watchdog and running agents
    keep a valid handle during the nightly rebuild; afterwards chunks of edited or deleted notes
    are pruned. Records for files this build does not read (session notes added by the
    watchdog) are kept while the file still exists.
    """
    chromadb, embedding_functions = _load_chroma_dependencies()

    resolved_vault_path = vault_path or get_vault_path()
    documents = [doc for doc in read_obsidian_vault(resolved_vault_path) if not _is_sync_conflict(doc.get("filepath"))]
    if not documents:
        LOGGER.warning("No Markdown documents found to index.")
        return 0

    ids, texts, metadatas = prepare_chunk_records(documents) if chunked else prepare_chroma_records(documents)
    if not ids:
        LOGGER.warning("No non-empty Markdown documents found to index.")
        return 0

    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        **({"metadata": {"chunked": True}} if chunked else {}),
    )

    indexed_count = _upsert_batches(
        collection,
        ids=ids,
        texts=texts,
        metadatas=metadatas,
        batch_size=batch_size,
    )
    if chunked:
        stale_ids = find_stale_chunk_ids(collection.get(include=["metadatas"]), ids, metadatas)
        for start in range(0, len(stale_ids), batch_size):
            collection.delete(ids=stale_ids[start:start + batch_size])
        LOGGER.info("Pruned %s stale chunks from collection '%s'.", len(stale_ids), collection_name)
    LOGGER.info("Successfully embedded %s documents into collection '%s'.", indexed_count, collection_name)
    return indexed_count


def find_stale_chunk_ids(
    existing: dict[str, Any],
    built_ids: list[str],
    built_metadatas: list[dict[str, Any]],
) -> list[str]:
    """Return ids left over from a previous build: whole-note records, chunks of rebuilt notes
    that no longer exist (the note got shorter), chunks of notes deleted from disk, and
    Syncthing conflict copies."""
    built = set(built_ids)
    rebuilt_paths = {metadata["filepath"] for metadata in built_metadatas}
    stale: list[str] = []
    for record_id, metadata in zip(existing.get("ids") or [], existing.get("metadatas") or []):
        if record_id in built:
            continue
        filepath = str((metadata or {}).get("filepath") or "")
        if ("chunk" not in (metadata or {}) or filepath in rebuilt_paths or not Path(filepath).is_file()
                or _is_sync_conflict(filepath)):
            stale.append(record_id)
    return stale


def get_chroma_collection(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Return a Chroma collection using the default embedding function.

    A collection created here is marked chunked unless it is the legacy whole-note one, so the
    watchdog starting before the first build still writes the chunk format.
    """
    chromadb, embedding_functions = _load_chroma_dependencies()
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
        **({} if collection_name == LEGACY_COLLECTION_NAME else {"metadata": {"chunked": True}}),
    )


def metadatas_to_wikilinks(metadatas: list[dict[str, Any]] | None) -> list[str]:
    """Convert Chroma metadata records into Obsidian wikilinks."""
    if not metadatas:
        return []

    backlinks: list[str] = []
    for metadata in metadatas:
        filename = str(metadata.get("filename") or "").strip()
        if not filename:
            continue

        clean_name = filename[:-3] if filename.lower().endswith(".md") else filename
        backlinks.append(f"[[{clean_name}]]")

    return backlinks


def _metadata_to_wikilink(metadata: dict[str, Any]) -> str | None:
    filename = str(metadata.get("filename") or "").strip()
    if not filename:
        return None

    clean_name = filename[:-3] if filename.lower().endswith(".md") else filename
    return f"[[{clean_name}]]"


def _query_results_to_notes(results: dict[str, Any]) -> list[dict[str, Any]]:
    """Normalize Chroma's nested query response into tool-friendly note results."""
    nested_metadatas = results.get("metadatas") or []
    metadatas = nested_metadatas[0] if nested_metadatas else []
    nested_documents = results.get("documents") or []
    documents = nested_documents[0] if nested_documents else []
    nested_distances = results.get("distances") or []
    distances = nested_distances[0] if nested_distances else []

    notes: list[dict[str, Any]] = []
    for index, metadata in enumerate(metadatas):
        wikilink = _metadata_to_wikilink(metadata)
        if not wikilink:
            continue

        content = str(documents[index]) if index < len(documents) and documents[index] is not None else ""
        distance = distances[index] if index < len(distances) else None
        note = {
            "wikilink": wikilink,
            "filename": str(metadata.get("filename") or ""),
            "filepath": str(metadata.get("filepath") or ""),
            "content": content,
        }
        if distance is not None:
            note["distance"] = distance
        notes.append(note)

    return notes


def _resolve_note_path(metadata: dict[str, Any], vault_path: Path) -> Path | None:
    filepath = str(metadata.get("filepath") or "").strip()
    if filepath:
        return Path(filepath).expanduser().resolve()

    filename = str(metadata.get("filename") or "").strip()
    if filename:
        return vault_path / filename

    return None


def _read_note_content_for_context(metadata: dict[str, Any], vault_path: Path) -> str | None:
    note_path = _resolve_note_path(metadata, vault_path)
    if note_path is None:
        return None

    try:
        return note_path.read_text(encoding="utf-8")
    except OSError:
        LOGGER.exception("Could not read note for agent context: %s", note_path)
        return None


def get_related_notes(
    query_text: str,
    n_results: int = 3,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> list[str]:
    """Return Obsidian wikilinks for notes closest to the query text."""
    if n_results < 1:
        raise ValueError("n_results must be at least 1")

    chromadb, embedding_functions = _load_chroma_dependencies()
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )
    except _missing_collection_errors(chromadb):
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return []

    if _is_chunked(collection):
        return metadatas_to_wikilinks([hit["metadata"] for hit in _query_unique_notes(collection, query_text, n_results)])

    results = collection.query(query_texts=[query_text], n_results=n_results)
    nested_metadatas = results.get("metadatas") or []
    first_result_metadatas = nested_metadatas[0] if nested_metadatas else []
    return metadatas_to_wikilinks(first_result_metadatas)


def search_second_brain_notes(
    search_query: str,
    num_results: int = 3,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
) -> list[dict[str, Any]]:
    """Search the local Obsidian Second Brain vector index and return structured note matches."""
    if num_results < 1:
        raise ValueError("num_results must be at least 1")

    chromadb, embedding_functions = _load_chroma_dependencies()
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )
    except _missing_collection_errors(chromadb):
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return []

    if _is_chunked(collection):
        notes: list[dict[str, Any]] = []
        for hit in _query_unique_notes(collection, search_query, num_results):
            metadata = hit["metadata"]
            wikilink = _section_wikilink(metadata)
            if not wikilink:
                continue
            note = {
                "wikilink": wikilink,
                "filename": str(metadata.get("filename") or ""),
                "filepath": str(metadata.get("filepath") or ""),
                "heading": str(metadata.get("heading") or ""),
                "content": "\n\n".join(hit["chunks"]),
            }
            if hit["distance"] is not None:
                note["distance"] = hit["distance"]
            notes.append(note)
        return notes

    results = collection.query(
        query_texts=[search_query],
        n_results=num_results,
        include=["documents", "metadatas", "distances"],
    )
    return _query_results_to_notes(results)


def search_second_brain(
    search_query: str,
    num_results: int = 3,
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    vault_path: Path | None = None,
) -> str:
    """Search the Second Brain and return raw Markdown note context for an LLM tool call."""
    if num_results < 1:
        raise ValueError("num_results must be at least 1")

    chromadb, embedding_functions = _load_chroma_dependencies()
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()

    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=embedding_function,
        )
    except _missing_collection_errors(chromadb):
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return "No relevant notes found in the Second Brain."

    if _is_chunked(collection):
        # Return the matched sections, not whole notes, so long notes don't flood the prompt.
        hits = _query_unique_notes(collection, search_query, num_results)
        sections = [
            f"### SOURCE NOTE: {hit['metadata'].get('filename')} ({_section_wikilink(hit['metadata'])})\n"
            + "\n\n[...]\n\n".join(hit["chunks"])
            for hit in hits
            if hit["metadata"].get("filename")
        ]
        if not sections:
            return "No relevant notes found in the Second Brain."
        return f"Found {len(sections)} related notes in the Second Brain:\n\n" + "\n\n".join(sections)

    results = collection.query(
        query_texts=[search_query],
        n_results=num_results,
        include=["metadatas"],
    )
    nested_metadatas = results.get("metadatas") or []
    metadatas = nested_metadatas[0] if nested_metadatas else []
    if not metadatas:
        return "No relevant notes found in the Second Brain."

    resolved_vault_path = vault_path or get_vault_path()
    sections: list[str] = []
    for metadata in metadatas:
        filename = str(metadata.get("filename") or "").strip()
        if not filename:
            continue

        content = _read_note_content_for_context(metadata, resolved_vault_path)
        if content is None:
            continue

        sections.append(f"### SOURCE NOTE: {filename}\n{content}")

    if not sections:
        return "No readable related notes found in the Second Brain."

    return f"Found {len(sections)} related notes in the Second Brain:\n\n" + "\n\n".join(sections)


def file_is_stable(file_path: Path, *, stability_seconds: float = DEFAULT_SESSION_STABILITY_SECONDS) -> bool:
    """Return True when a file has not been modified recently."""
    if stability_seconds <= 0:
        return True

    last_modified = file_path.stat().st_mtime
    return time.time() - last_modified >= stability_seconds


def process_session_file(
    file_path: Path,
    collection: Any,
    *,
    n_results: int = 3,
    stability_seconds: float = DEFAULT_SESSION_STABILITY_SECONDS,
    commit_vault: bool = False,
    commit_reason: str | None = None,
) -> bool:
    """
    Add related-note backlinks to one session file and upsert it into Chroma.

    Returns True when the file was processed, False when it was skipped.
    """
    if file_path.suffix.lower() != ".md":
        return False
    if not file_is_stable(file_path, stability_seconds=stability_seconds):
        return False

    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError:
        LOGGER.exception("Could not read session file: %s", file_path)
        return False

    if RELATED_CONCEPTS_HEADER in content:
        return False

    LOGGER.info("New session detected: %s. Processing...", file_path.name)
    chunked = _is_chunked(collection)
    if chunked:
        first_result_metadatas = [hit["metadata"] for hit in _query_unique_notes(collection, content, n_results)]
    else:
        results = collection.query(query_texts=[content], n_results=n_results)
        nested_metadatas = results.get("metadatas") or []
        first_result_metadatas = nested_metadatas[0] if nested_metadatas else []
    related_links = metadatas_to_wikilinks(first_result_metadatas)
    updated_content = append_related_concepts(content, related_links)

    if related_links:
        from .vault_write_gate import require_vault_write
        require_vault_write(
            commit_vault=commit_vault,
            commit_reason=commit_reason,
            operation="session backlink update",
            target=file_path,
        )
        try:
            file_path.write_text(f"{updated_content}\n", encoding="utf-8")
        except OSError:
            LOGGER.exception("Could not write backlinks to session file: %s", file_path)
            return False
        LOGGER.info("Backlinks appended to %s", file_path.name)

    if chunked:
        ids, texts, metadatas = prepare_chunk_records(
            [{"filename": file_path.name, "filepath": str(file_path), "content": updated_content}]
        )
        collection.delete(where={"filepath": str(file_path.resolve())})
        if ids:
            collection.upsert(documents=texts, metadatas=metadatas, ids=ids)
    else:
        collection.upsert(
            documents=[updated_content],
            metadatas=[{"filename": file_path.name, "filepath": str(file_path.resolve())}],
            ids=[str(file_path.resolve())],
        )
    LOGGER.info("%s embedded into the local vector DB.", file_path.name)
    return True


def process_unlinked_sessions(
    sessions_dir: Path,
    collection: Any,
    *,
    n_results: int = 3,
    stability_seconds: float = DEFAULT_SESSION_STABILITY_SECONDS,
    commit_vault: bool = False,
    commit_reason: str | None = None,
) -> int:
    """Process all stable, unlinked Markdown session files in the sessions directory."""
    processed_count = 0
    for file_path in sorted(sessions_dir.glob("*.md")):
        if process_session_file(
            file_path,
            collection,
            n_results=n_results,
            stability_seconds=stability_seconds,
            commit_vault=commit_vault,
            commit_reason=commit_reason,
        ):
            processed_count += 1

    return processed_count


def run_session_watchdog(
    *,
    interval_seconds: float = 10.0,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
    n_results: int = 3,
    stability_seconds: float = DEFAULT_SESSION_STABILITY_SECONDS,
    commit_vault: bool = False,
    commit_reason: str | None = None,
) -> None:
    """Continuously monitor Agent_Sessions and link new stable session notes."""
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than 0")

    LOGGER.info("Starting sync-safe vault watchdog...")
    sessions_dir = get_sessions_dir()
    collection = get_chroma_collection(db_path=db_path, collection_name=collection_name)
    LOGGER.info("Monitoring folder: %s", sessions_dir)

    try:
        while True:
            process_unlinked_sessions(
                sessions_dir,
                collection,
                n_results=n_results,
                stability_seconds=stability_seconds,
                commit_vault=commit_vault,
                commit_reason=commit_reason,
            )
            time.sleep(interval_seconds)
    except KeyboardInterrupt:
        LOGGER.info("Watchdog stopped by user.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description="Build the Second Brain vector index from the Obsidian vault.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION_NAME)
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH)
    parser.add_argument("--whole-notes", action="store_true", help="Legacy mode: one record per note, no chunking.")
    cli_args = parser.parse_args()
    build_vector_database(db_path=cli_args.db_path, collection_name=cli_args.collection, chunked=not cli_args.whole_notes)
