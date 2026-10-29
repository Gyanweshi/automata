import pytest

from agency_common import rag_eval
from agency_common.rag_eval import evaluate_collection, load_questions


def test_evaluate_collection_scores_rank_of_first_expected_note(monkeypatch, tmp_path):
    results = {
        "q1": [{"filepath": str(tmp_path / "A.md"), "wikilink": "[[A]]"}],
        "q2": [{"filepath": str(tmp_path / "X.md"), "wikilink": "[[X]]"}, {"filepath": str(tmp_path / "B.md"), "wikilink": "[[B]]"}],
        "q3": [{"filepath": str(tmp_path / "X.md"), "wikilink": "[[X]]"}],
    }
    monkeypatch.setattr(rag_eval, "search_second_brain_notes", lambda question, **kwargs: results[question])
    questions = [
        {"question": "q1", "expect": ["A.md"]},
        {"question": "q2", "expect": ["B.md", "C.md"]},
        {"question": "q3", "expect": ["C.md"]},
    ]

    report = evaluate_collection(questions, collection_name="c", vault_path=tmp_path, k=3)

    assert [row["rank"] for row in report["rows"]] == [1, 2, None]
    assert report["hit_at_1"] == pytest.approx(1 / 3)
    assert report["hit_at_k"] == pytest.approx(2 / 3)
    assert report["mrr"] == pytest.approx((1 + 0.5) / 3)


def test_load_questions_rejects_entries_without_expectations(tmp_path):
    path = tmp_path / "questions.yaml"
    path.write_text("- question: what?\n", encoding="utf-8")

    with pytest.raises(ValueError, match="expect"):
        load_questions(path)
