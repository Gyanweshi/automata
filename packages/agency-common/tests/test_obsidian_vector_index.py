
import pytest

from agency_common.obsidian_vector_index import (
    VectorIndexError,
    get_related_notes,
    _load_chroma_dependencies,
    _upsert_batches,
    file_is_stable,
    metadatas_to_wikilinks,
    process_session_file,
    process_unlinked_sessions,
    prepare_chroma_records,
    search_second_brain,
    search_second_brain_notes,
)


def test_prepare_chroma_records_uses_filepath_as_id_and_flat_metadata(tmp_path):
    note_path = tmp_path / "Concept.md"
    note_path.write_text("# Concept", encoding="utf-8")

    ids, texts, metadatas = prepare_chroma_records(
        [
            {
                "filename": "Concept.md",
                "filepath": str(note_path),
                "metadata": {"tags": ["ai"]},
                "content": "# Concept\nUseful context",
            }
        ]
    )

    assert ids == [str(note_path.resolve())]
    assert texts == ["# Concept\nUseful context"]
    assert metadatas == [{"filename": "Concept.md", "filepath": str(note_path.resolve())}]


def test_prepare_chroma_records_skips_empty_documents(tmp_path):
    note_path = tmp_path / "Empty.md"

    ids, texts, metadatas = prepare_chroma_records(
        [
            {
                "filename": "Empty.md",
                "filepath": str(note_path),
                "metadata": {},
                "content": "  \n",
            }
        ]
    )

    assert ids == []
    assert texts == []
    assert metadatas == []


def test_upsert_batches_writes_in_chunks():
    class FakeCollection:
        def __init__(self):
            self.calls = []

        def upsert(self, *, documents, metadatas, ids):
            self.calls.append({"documents": documents, "metadatas": metadatas, "ids": ids})

    collection = FakeCollection()

    count = _upsert_batches(
        collection,
        ids=["1", "2", "3"],
        texts=["one", "two", "three"],
        metadatas=[{"filename": "1.md"}, {"filename": "2.md"}, {"filename": "3.md"}],
        batch_size=2,
    )

    assert count == 3
    assert collection.calls == [
        {
            "documents": ["one", "two"],
            "metadatas": [{"filename": "1.md"}, {"filename": "2.md"}],
            "ids": ["1", "2"],
        },
        {
            "documents": ["three"],
            "metadatas": [{"filename": "3.md"}],
            "ids": ["3"],
        },
    ]


def test_upsert_batches_rejects_invalid_batch_size():
    with pytest.raises(ValueError, match="batch_size"):
        _upsert_batches(
            object(),
            ids=[],
            texts=[],
            metadatas=[],
            batch_size=0,
        )


def test_metadatas_to_wikilinks_strips_markdown_extension():
    assert metadatas_to_wikilinks(
        [
            {"filename": "Concept.md"},
            {"filename": "Evergreen Note.MD"},
            {"filename": "NoExtension"},
            {"filename": ""},
            {},
        ]
    ) == ["[[Concept]]", "[[Evergreen Note]]", "[[NoExtension]]"]


def test_get_related_notes_queries_collection_and_formats_results(monkeypatch, tmp_path):
    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeCollection:
        def query(self, *, query_texts, n_results):
            assert query_texts == ["agent repo vs second brain"]
            assert n_results == 2
            return {"metadatas": [[{"filename": "Agent Repo.md"}, {"filename": "Second Brain.md"}]]}

    class FakeClient:
        def __init__(self, path):
            assert path == str(tmp_path)

        def get_collection(self, *, name, embedding_function):
            assert name == "second_brain"
            return FakeCollection()

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert get_related_notes("agent repo vs second brain", n_results=2, db_path=tmp_path) == [
        "[[Agent Repo]]",
        "[[Second Brain]]",
    ]


def test_get_related_notes_returns_empty_when_collection_missing(monkeypatch, tmp_path):
    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeClient:
        def __init__(self, path):
            pass

        def get_collection(self, *, name, embedding_function):
            raise ValueError("missing")

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert get_related_notes("anything", db_path=tmp_path) == []


def test_get_related_notes_rejects_invalid_result_count():
    with pytest.raises(ValueError, match="n_results"):
        get_related_notes("anything", n_results=0)


def test_search_second_brain_notes_returns_structured_note_results(monkeypatch, tmp_path):
    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeCollection:
        def query(self, *, query_texts, n_results, include):
            assert query_texts == ["API architecture blueprint"]
            assert n_results == 2
            assert include == ["documents", "metadatas", "distances"]
            return {
                "documents": [["Blueprint content", "Rendering content"]],
                "metadatas": [[
                    {"filename": "API Blueprint.md", "filepath": "/vault/API Blueprint.md"},
                    {"filename": "Next Rendering.md", "filepath": "/vault/Next Rendering.md"},
                ]],
                "distances": [[0.12, 0.34]],
            }

    class FakeClient:
        def __init__(self, path):
            assert path == str(tmp_path)

        def get_collection(self, *, name, embedding_function):
            assert name == "second_brain"
            return FakeCollection()

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert search_second_brain_notes("API architecture blueprint", num_results=2, db_path=tmp_path) == [
        {
            "wikilink": "[[API Blueprint]]",
            "filename": "API Blueprint.md",
            "filepath": "/vault/API Blueprint.md",
            "content": "Blueprint content",
            "distance": 0.12,
        },
        {
            "wikilink": "[[Next Rendering]]",
            "filename": "Next Rendering.md",
            "filepath": "/vault/Next Rendering.md",
            "content": "Rendering content",
            "distance": 0.34,
        },
    ]


def test_search_second_brain_notes_returns_empty_when_collection_missing(monkeypatch, tmp_path):
    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeClient:
        def __init__(self, path):
            pass

        def get_collection(self, *, name, embedding_function):
            raise ValueError("missing")

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert search_second_brain_notes("anything", db_path=tmp_path) == []


def test_search_second_brain_notes_rejects_invalid_result_count():
    with pytest.raises(ValueError, match="num_results"):
        search_second_brain_notes("anything", num_results=0)


def test_search_second_brain_returns_raw_note_context(monkeypatch, tmp_path):
    vault_path = tmp_path / "vault"
    nested = vault_path / "Projects"
    nested.mkdir(parents=True)
    note_path = nested / "API Blueprint.md"
    note_path.write_text("# API Blueprint\nRaw markdown context", encoding="utf-8")

    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeCollection:
        def query(self, *, query_texts, n_results, include):
            assert query_texts == ["API architecture blueprint"]
            assert n_results == 1
            assert include == ["metadatas"]
            return {
                "metadatas": [[
                    {"filename": "API Blueprint.md", "filepath": str(note_path)},
                ]]
            }

    class FakeClient:
        def __init__(self, path):
            pass

        def get_collection(self, *, name, embedding_function):
            return FakeCollection()

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    context = search_second_brain(
        "API architecture blueprint",
        num_results=1,
        db_path=tmp_path,
        vault_path=vault_path,
    )

    assert context == (
        "Found 1 related notes in the Second Brain:\n\n"
        "### SOURCE NOTE: API Blueprint.md\n# API Blueprint\nRaw markdown context"
    )


def test_search_second_brain_falls_back_to_vault_filename(monkeypatch, tmp_path):
    vault_path = tmp_path / "vault"
    vault_path.mkdir()
    note_path = vault_path / "Flat Note.md"
    note_path.write_text("Flat note content", encoding="utf-8")

    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeCollection:
        def query(self, *, query_texts, n_results, include):
            return {"metadatas": [[{"filename": "Flat Note.md"}]]}

    class FakeClient:
        def __init__(self, path):
            pass

        def get_collection(self, *, name, embedding_function):
            return FakeCollection()

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert "Flat note content" in search_second_brain("flat", db_path=tmp_path, vault_path=vault_path)


def test_search_second_brain_returns_message_when_no_matches(monkeypatch, tmp_path):
    class FakeEmbeddingFunctions:
        class DefaultEmbeddingFunction:
            pass

    class FakeCollection:
        def query(self, *, query_texts, n_results, include):
            return {"metadatas": [[]]}

    class FakeClient:
        def __init__(self, path):
            pass

        def get_collection(self, *, name, embedding_function):
            return FakeCollection()

    class FakeChroma:
        PersistentClient = FakeClient

    monkeypatch.setattr(
        "agency_common.obsidian_vector_index._load_chroma_dependencies",
        lambda: (FakeChroma, FakeEmbeddingFunctions),
    )

    assert search_second_brain("missing", db_path=tmp_path) == "No relevant notes found in the Second Brain."


def test_search_second_brain_rejects_invalid_result_count():
    with pytest.raises(ValueError, match="num_results"):
        search_second_brain("anything", num_results=0)


def test_file_is_stable_accepts_zero_stability_window(tmp_path):
    note_path = tmp_path / "Session.md"
    note_path.write_text("content", encoding="utf-8")

    assert file_is_stable(note_path, stability_seconds=0)


def test_process_session_file_skips_recent_file(monkeypatch, tmp_path):
    class FakeCollection:
        def query(self, *, query_texts, n_results):
            raise AssertionError("recent files should not be queried")

    note_path = tmp_path / "Session.md"
    note_path.write_text("content", encoding="utf-8")
    monkeypatch.setattr("agency_common.obsidian_vector_index.time.time", lambda: note_path.stat().st_mtime)

    assert not process_session_file(note_path, FakeCollection(), stability_seconds=5)


def test_process_session_file_appends_backlinks_and_upserts(tmp_path):
    class FakeCollection:
        def __init__(self):
            self.upserts = []

        def query(self, *, query_texts, n_results):
            assert query_texts == ["Session transcript"]
            assert n_results == 2
            return {"metadatas": [[{"filename": "Architecture.md"}, {"filename": "Agents.md"}]]}

        def upsert(self, *, documents, metadatas, ids):
            self.upserts.append({"documents": documents, "metadatas": metadatas, "ids": ids})

    note_path = tmp_path / "Session.md"
    note_path.write_text("Session transcript", encoding="utf-8")
    collection = FakeCollection()

    assert process_session_file(
        note_path,
        collection,
        n_results=2,
        stability_seconds=0,
        commit_vault=True,
        commit_reason="approved test output",
    )

    updated_content = note_path.read_text(encoding="utf-8")
    assert "### Related Concepts\n- [[Architecture]]\n- [[Agents]]" in updated_content
    assert collection.upserts == [
        {
            "documents": [updated_content.rstrip("\n")],
            "metadatas": [{"filename": "Session.md", "filepath": str(note_path.resolve())}],
            "ids": [str(note_path.resolve())],
        }
    ]


def test_process_session_file_skips_already_linked_file(tmp_path):
    class FakeCollection:
        def query(self, *, query_texts, n_results):
            raise AssertionError("linked files should not be queried")

    note_path = tmp_path / "Session.md"
    note_path.write_text("Session transcript\n\n### Related Concepts\n- [[Architecture]]", encoding="utf-8")

    assert not process_session_file(note_path, FakeCollection(), stability_seconds=0)


def test_process_session_file_embeds_without_rewrite_when_no_links(tmp_path):
    class FakeCollection:
        def __init__(self):
            self.upserts = []

        def query(self, *, query_texts, n_results):
            return {"metadatas": [[]]}

        def upsert(self, *, documents, metadatas, ids):
            self.upserts.append({"documents": documents, "metadatas": metadatas, "ids": ids})

    note_path = tmp_path / "Session.md"
    note_path.write_text("Session transcript", encoding="utf-8")
    collection = FakeCollection()

    assert process_session_file(note_path, collection, stability_seconds=0)
    assert note_path.read_text(encoding="utf-8") == "Session transcript"
    assert collection.upserts[0]["documents"] == ["Session transcript"]


def test_process_unlinked_sessions_counts_only_processed_markdown(tmp_path):
    class FakeCollection:
        def query(self, *, query_texts, n_results):
            return {"metadatas": [[{"filename": "Architecture.md"}]]}

        def upsert(self, *, documents, metadatas, ids):
            pass

    (tmp_path / "Session_1.md").write_text("Session one", encoding="utf-8")
    (tmp_path / "Session_2.md").write_text("Session two\n\n### Related Concepts\n- [[Done]]", encoding="utf-8")
    (tmp_path / ".syncthing.tmp").write_text("temp", encoding="utf-8")

    assert process_unlinked_sessions(
        tmp_path,
        FakeCollection(),
        stability_seconds=0,
        commit_vault=True,
        commit_reason="approved test output",
    ) == 1


def test_load_chroma_dependencies_reports_missing_dependency(monkeypatch):
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "chromadb":
            raise ImportError("missing chroma")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    with pytest.raises(VectorIndexError, match="chromadb is not installed"):
        _load_chroma_dependencies()
