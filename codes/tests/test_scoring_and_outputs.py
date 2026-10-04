import json

import numpy as np
import pandas as pd
import pytest

from modules import judging, outputs, scoring, snowball, specter, zotero
from modules.ris import to_ris


def frame_of(rows):
    return pd.DataFrame(rows)


def test_pct_rank_uses_average_for_ties():
    ranks = scoring.pct_rank(pd.Series([0, 0, 0, 0, 5]))
    assert ranks.iloc[0] == pytest.approx(0.5)      # a block of zeros sits mid-range, not near the top
    assert ranks.iloc[4] == pytest.approx(1.0)


def test_coupling_is_nan_without_references_and_counts_overlap():
    frame = frame_of([{"doi": "a", "references_count": 4}, {"doi": "b", "references_count": 0}])
    references = {"a": [{"doi": "seed1"}, {"doi": "r1"}, {"doi": "r2"}, {"author": "Book"}], "b": []}
    seed_data = {"seed1": {"ref_dois": ["r1"]}, "seed2": {"ref_dois": ["r1", "r9"]}}
    result = scoring.add_coupling(frame, references, seed_data, direct_weight=3.0)
    assert result.loc[0, "n_cites_seed"] == 1 and result.loc[0, "n_shared_refs"] == 1
    assert result.loc[0, "coupling"] == pytest.approx((3 * 1 + 1) / 2)
    assert np.isnan(result.loc[1, "coupling"])


def test_coupling_leave_one_out_for_a_seed():
    frame = frame_of([{"doi": "seed1", "references_count": 1}])
    references = {"seed1": [{"doi": "r1"}]}
    alone = scoring.add_coupling(frame.copy(), references, {"seed1": {"ref_dois": ["r1"]}}, 3.0)
    assert alone.loc[0, "n_shared_refs"] == 0       # only its own list cites r1
    shared = scoring.add_coupling(frame.copy(), references,
                                  {"seed1": {"ref_dois": ["r1"]}, "seed2": {"ref_dois": ["r1"]}}, 3.0)
    assert shared.loc[0, "n_shared_refs"] == 1


def test_composite_renormalises_over_available_signals():
    frame = frame_of([{"coupling": np.nan, "tfidf": 0.9, "has_abstract": True},
                      {"coupling": 1.0, "tfidf": 0.1, "has_abstract": True},
                      {"coupling": 0.0, "tfidf": 0.5, "has_abstract": True}])
    result, signals = scoring.add_composite(frame, {"coupling": 0.4, "specter": 0.4, "tfidf": 0.2})
    assert signals == ["coupling", "tfidf"]
    assert result.loc[0, "composite"] == pytest.approx(1.0)   # only tf-idf present: its percentile alone
    assert result.loc[0, "n_signals"] == 1 and result.loc[1, "n_signals"] == 2
    assert scoring.level_of(0.96) == "Very High" and scoring.level_of(0.5) == "Normal"


def test_tfidf_prefers_matching_text():
    frame = frame_of([{"title": "Candidate selection in regional parties", "abstract": ""},
                      {"title": "Protein folding dynamics", "abstract": ""},
                      {"title": "Regional parties and candidate selection rules", "abstract": ""}])
    result = scoring.add_tfidf(frame, [("doc", "regional parties choose candidate selection rules")])
    assert result.loc[1, "tfidf"] < result.loc[0, "tfidf"]


def test_library_link_encodes_title_and_drops_commas():
    template = "https://lib.example/search?query=any,contains,{title}&vid=X"
    link = outputs.library_link(template, "Parties, voters & elections: a study")
    assert link == "https://lib.example/search?query=any,contains,Parties%20voters%20%26%20elections%3A%20a%20study&vid=X"
    assert outputs.library_link(template, "") == ""


def shortlist_frame():
    rows = []
    for journal, relevances in (("A", [5, 5, 4, 4]), ("B", [4, 2, 2]), ("C", [1])):
        for index, relevance in enumerate(relevances):
            rows.append({"item_id": f"{journal}{index}", "journal": journal, "agent_relevance": relevance,
                         "composite_pct": 0.9 - index * 0.1, "composite": 0.5})
    return frame_of(rows)


def test_shortlist_global_takes_best_overall():
    picked = outputs.allocate_shortlist(shortlist_frame(), 3, "global", 3)
    assert list(picked["item_id"]) == ["A0", "A1", "B0"]


def test_shortlist_per_journal_quota_floor_and_redistribution():
    frame = shortlist_frame()
    picked = outputs.allocate_shortlist(frame, 6, "per-journal", 3, redistribute=True)
    # quota 2 each: A0 A1, B0 (only one eligible in B), none from C; 3 spare places -> A2 A3
    assert set(picked["item_id"]) == {"A0", "A1", "B0", "A2", "A3"}
    strict = outputs.allocate_shortlist(frame, 6, "per-journal", 3, redistribute=False)
    assert set(strict["item_id"]) == {"A0", "A1", "B0"}


def test_shortlist_without_judgments_falls_back_to_scores():
    frame = shortlist_frame().assign(agent_relevance=np.nan)
    picked = outputs.allocate_shortlist(frame, 2, "global", 3)
    assert len(picked) == 2 and set(picked["composite_pct"]) == {0.9}


def test_workbook_round_trip_reads_marks_by_item_id(tmp_path):
    path = tmp_path / "shortlist.xlsx"
    rows = [{"rank": i, outputs.MARK_COLUMN: mark, "title": f"T{i}", "doi-link": f"https://doi.org/10.1/{i}",
             "item_id": f"10.1/{i}"} for i, mark in enumerate(["yes", "", "No", "YES ", "maybe"], 1)]
    outputs.write_workbook(path, [{"name": "shortlist", "columns": ["rank", outputs.MARK_COLUMN, "title", "doi-link", "item_id"],
                                   "rows": rows[::-1], "links": ("doi-link",), "dropdown": outputs.MARK_COLUMN}])
    selected, counts, odd = outputs.read_marks(path, ["shortlist", "snowball"])
    assert sorted(r["item_id"] for r in selected) == ["10.1/1", "10.1/4"]
    assert counts == {"shortlist": {"rows": 5, "marked_yes": 2}}
    assert len(odd) == 1 and "maybe" in odd[0]


def test_read_marks_requires_item_id_column(tmp_path):
    path = tmp_path / "broken.xlsx"
    outputs.write_workbook(path, [{"name": "shortlist", "columns": [outputs.MARK_COLUMN, "title"],
                                   "rows": [{outputs.MARK_COLUMN: "yes", "title": "T"}]}])
    with pytest.raises(ValueError):
        outputs.read_marks(path, ["shortlist"])


def test_excel_lock_file_detection(tmp_path):
    path = tmp_path / "shortlist.xlsx"
    assert outputs.excel_lock_file(path) is None
    (tmp_path / "~$shortlist.xlsx").write_text("")
    assert outputs.excel_lock_file(path) is not None


def test_merge_judgments_reports_missing_and_invalid(tmp_path):
    (tmp_path / "judged-001.json").write_text(json.dumps([
        {"item_id": "a", "relevance": 5, "reason": "good", "theme": "x"},
        {"item_id": "b", "relevance": 9, "reason": "bad score", "theme": "x"},
        {"item_id": "c", "relevance": 3, "reason": " ", "theme": "x"}]), encoding="utf-8")
    judgments, problems = judging.merge_judgments(tmp_path, ["a", "b", "c", "d"])
    assert list(judgments) == ["a"] and judgments["a"]["agent_relevance"] == 5
    assert len(problems) == 3 and any("not judged yet" in p for p in problems)
    # a judgment left over from an earlier run is ignored rather than treated as an error
    judgments, problems = judging.merge_judgments(tmp_path, [])
    assert judgments == {} and len(problems) == 2


def test_select_for_judging_adds_each_journals_top_slice():
    frame = frame_of([{"item_id": f"A{i}", "journal": "A", "composite_pct": 0.9 - i * 0.01, "composite": 0.5} for i in range(6)]
                     + [{"item_id": "B0", "journal": "B", "composite_pct": 0.1, "composite": 0.1}])
    only_global = judging.select_for_judging(frame, 2, 1, "global", ["A", "B"])
    assert "B0" not in set(only_global["item_id"])
    per_journal = judging.select_for_judging(frame, 2, 1, "per-journal", ["A", "B"])
    assert "B0" in set(per_journal["item_id"])


def test_snowball_groups_references_and_counts_sources():
    book = {"author": "Sartori G", "year": "1976", "volume_title": "Parties and Party Systems: A Framework"}
    sources = [("s1", "One (2020)", [{"doi": "10.1/x"}, book]),
               ("s2", "Two (2021)", [{"doi": "10.1/x"}, dict(book, year="2005")]),
               ("s3", "Three (2022)", [{"unstructured": "short"}])]
    by_doi, by_key, labels = snowball.collect(sources)
    assert by_doi["10.1/x"] == {"s1", "s2"}
    assert len(by_key) == 1 and next(iter(by_key.values()))["sources"] == {"s1", "s2"}
    rows = snowball.build_rows(by_doi, by_key, labels, {"10.1/x": {
        "title": "An article", "authors_str": "A, B", "year": "2001", "journal": "J", "publisher": "",
        "type": "journal-article", "abstract": "", "issns": ["1234-5678"]}}, 2, set(), set(), {"1234-5678"})
    assert {r["item_id"].startswith("ref:") for r in rows} == {True, False}
    assert next(r for r in rows if r["doi"])["in_journal_list"] is True
    assert next(r for r in rows if not r["doi"])["type"] == "book"


def test_ris_entry_has_core_fields():
    record = {"type": "journal-article", "title": "A title", "journal": "Party Politics", "year": "2020",
              "authors": [{"family": "Van der Meer", "given": "Tom"}], "editors": [], "volume": "26",
              "issue": "2", "pages": "120-132", "doi": "10.1/x", "url": "", "abstract": "", "publisher": "SAGE"}
    lines = to_ris(record, keywords=["k"]).split("\r\n")
    assert lines[0] == "TY  - JOUR" and lines[-1] == "ER  - "
    assert "AU  - Van der Meer, Tom" in lines and "SP  - 120" in lines and "EP  - 132" in lines
    assert not any(line.startswith("PB") for line in lines)   # publisher omitted for journal articles


def test_merge_rdf_combines_documents():
    template = ('<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
                'xmlns:bib="http://purl.org/net/biblio#"><bib:Article rdf:about="{}"/></rdf:RDF>')
    merged = zotero.merge_rdf([template.format("a"), template.format("b")])
    assert merged.count("<bib:Article") == 2 and merged.count("<rdf:RDF") == 1
    assert zotero.merge_rdf([]) == ""


def test_zotero_item_uses_only_template_fields(monkeypatch):
    client = zotero.Zotero("key", "group", "123")
    templates = {"journalArticle": {"itemType": "journalArticle", "title": "", "publicationTitle": "", "DOI": "",
                                    "date": "", "extra": "", "creators": [], "tags": [], "collections": []},
                 "book": {"itemType": "book", "title": "", "publisher": "", "date": "", "extra": "",
                          "creators": [], "tags": [], "collections": []}}
    monkeypatch.setattr(client, "template", lambda item_type: dict(templates[item_type]))
    record = {"type": "journal-article", "title": "T", "journal": "J", "year": "2020", "doi": "10.1/x",
              "authors": [{"family": "Van der Meer", "given": "Tom"}], "editors": [], "volume": "9"}
    item = client.build_item(record, "10.1/x", "COLL", ["tag"])
    assert item["publicationTitle"] == "J" and item["DOI"] == "10.1/x" and "volume" not in item
    assert item["creators"] == [{"creatorType": "author", "lastName": "Van der Meer", "firstName": "Tom"}]
    assert item["collections"] == ["COLL"] and item["extra"].startswith("lit-review-id: 10.1/x")
    book = client.build_item({**record, "type": "monograph", "publisher": "CUP"}, "10.1/x", "", ["tag"])
    assert book["itemType"] == "book" and book["publisher"] == "CUP"
    assert book["extra"].splitlines()[0] == "DOI: 10.1/x"      # books have no DOI field


def test_zotero_settings_validation():
    ok = zotero.settings_from_env({"ZOTERO_API_KEY": "k", "ZOTERO_GROUP_ID": "42"})
    assert ok == {"api_key": "k", "library_type": "group", "library_id": "42"}
    with pytest.raises(zotero.ZoteroError):
        zotero.settings_from_env({"ZOTERO_API_KEY": "k"})


def test_specter_windows_and_setting_off():
    assert specter.windows("") == []
    assert len(specter.windows("x" * 4000)) == 3
    assert len(specter.windows("x" * 500000)) == specter.MAX_WINDOWS
    assert specter.resolve_setting("off", 100) == (False, {})


def test_specter_check_reports_environment():
    info = specter.check(1000)
    assert set(info) >= {"torch_installed", "nvidia_gpu", "model_cached", "recommendation", "setup_steps"}
    assert info["recommendation"] in ("on", "off")
