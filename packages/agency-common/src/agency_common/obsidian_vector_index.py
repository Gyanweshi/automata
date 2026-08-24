"""Build and query a local ChromaDB index from Obsidian Markdown notes."""
from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from .knowledge_reader import get_vault_path, read_obsidian_vault
from .obsidian_writer import append_related_concepts, get_sessions_dir

LOGGER = logging.getLogger(__name__)
DEFAULT_DB_PATH = "./chroma_db"
DEFAULT_COLLECTION_NAME = "second_brain"
DEFAULT_BATCH_SIZE = 100
DEFAULT_SESSION_STABILITY_SECONDS = 5.0
RELATED_CONCEPTS_HEADER = "### Related Concepts"


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
) -> int:
    """Read the Obsidian vault and embed Markdown notes into a persistent ChromaDB collection."""
    chromadb, embedding_functions = _load_chroma_dependencies()

    resolved_vault_path = vault_path or get_vault_path()
    documents = read_obsidian_vault(resolved_vault_path)
    if not documents:
        LOGGER.warning("No Markdown documents found to index.")
        return 0

    ids, texts, metadatas = prepare_chroma_records(documents)
    if not ids:
        LOGGER.warning("No non-empty Markdown documents found to index.")
        return 0

    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
    )

    indexed_count = _upsert_batches(
        collection,
        ids=ids,
        texts=texts,
        metadatas=metadatas,
        batch_size=batch_size,
    )
    LOGGER.info("Successfully embedded %s documents into collection '%s'.", indexed_count, collection_name)
    return indexed_count


def get_chroma_collection(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    collection_name: str = DEFAULT_COLLECTION_NAME,
):
    """Return a Chroma collection using the default embedding function."""
    chromadb, embedding_functions = _load_chroma_dependencies()
    client = chromadb.PersistentClient(path=str(db_path))
    embedding_function = embedding_functions.DefaultEmbeddingFunction()
    return client.get_or_create_collection(
        name=collection_name,
        embedding_function=embedding_function,
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
    except ValueError:
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return []

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
    except ValueError:
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return []

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
    except ValueError:
        LOGGER.error("Collection '%s' does not exist. Run build_vector_database() first.", collection_name)
        return "No relevant notes found in the Second Brain."

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
    build_vector_database()
