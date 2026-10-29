from agency_common import vault_search


def test_vault_search_joins_query_words_and_prints_context(monkeypatch, capsys):
    calls = []

    def fake_search(query, **kwargs):
        calls.append((query, kwargs["num_results"], kwargs["collection_name"]))
        return "Found 1 related notes"

    monkeypatch.setattr(vault_search, "search_second_brain", fake_search)

    assert vault_search.main(["ethanol", "petrol", "claims", "-n", "2", "--collection", "c"]) == 0
    assert calls == [("ethanol petrol claims", 2, "c")]
    assert capsys.readouterr().out == "Found 1 related notes\n"
