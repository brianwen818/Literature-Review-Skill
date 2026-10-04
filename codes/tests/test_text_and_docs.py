from modules import docs, keywords, seeds
from modules.crossref import clean_query, consistent_match, parse_item
from modules.textutil import find_doi, noise_reason, normalize_doi, normalize_title


def test_normalize_doi_variants():
    assert normalize_doi("https://doi.org/10.1177/ABC.") == "10.1177/abc"
    assert normalize_doi("doi: 10.1/x") == "10.1/x"
    assert normalize_doi(None) == ""
    assert normalize_doi(float("nan")) == ""


def test_find_doi_in_citation():
    text = "Adams, J. (2010). Title. Public Choice, 145, 417-433. https://doi.org/10.1007/s11127-009-9573-1"
    assert find_doi(text) == "10.1007/s11127-009-9573-1"
    assert find_doi("no doi here") == ""


def test_normalize_title_folds_accents_and_punctuation():
    assert normalize_title("Solé-Ollé: The “Effects”") == "sole olle the effects"


def test_noise_reason_catches_reviews_and_front_matter():
    assert noise_reason("Book review: Democratizing Candidate Selection") == "book_review"
    assert noise_reason("Japanese Electoral Politics. Edited by Steven R. Reed. London: RoutledgeCurzon, 2003") == "book_review"
    assert noise_reason("James Mitchell, The Scottish National Party, reviewed by Peter Lynch") == "book_review"
    assert noise_reason("Erratum to: Party systems") == "correction"
    assert noise_reason("Issue Information") == "front_matter"
    assert noise_reason("") == "no_title"


def test_noise_reason_keeps_research_articles():
    for title in ("Candidate Selection Methods: An Analytical Framework",
                  "Reviewing the evidence on party switching",
                  "The index of party nationalization revisited",
                  "Corrections and prisons policy in comparative perspective"):
        assert noise_reason(title) == "", title


def test_split_references_markdown_heading():
    text = "# Intro\n" + "body line\n" * 20 + "# **References**\n\n[Smith J (2020) A title here. *Journal* 1(2): 3–4.](http://x)\n"
    body, refs = docs.split_references(text)
    assert "body line" in body and "Smith J" not in body
    assert "Smith J (2020)" in refs


def test_split_references_ignores_early_mention():
    text = "References\n" + "body\n" * 50
    body, refs = docs.split_references(text)
    assert refs == "" and body == text


def test_reference_entries_join_wrapped_lines():
    refs = ("Anckar, Carsten (1998) Storlek och partisystem: en studie av 77 stater. Åbo: Åbo\n"
            "Akademis förlag.\n"
            "Bille, Lars (2001) ‘Democratizing a Democratic Procedure: Myth or Reality?’, Party\n"
            "Politics 7: 363–80.\n"
            "Dahl, Robert and Edward Tufte (1973) Size and Democracy. Stanford, CA: Stanford\n"
            "University Press.\n")
    entries = docs.split_reference_entries(refs)
    assert len(entries) == 3
    assert entries[1].startswith("Bille, Lars (2001)") and entries[1].endswith("363–80.")


def test_reference_entries_numbered_list():
    refs = "\n".join(f"[{i}] Author{i} A. (20{10 + i}) A sufficiently long title number {i}. Journal {i}: 1-2."
                     for i in range(1, 6))
    entries = docs.split_reference_entries(refs)
    assert len(entries) == 5 and entries[0].startswith("Author1")


def test_ngrams_do_not_cross_punctuation_or_start_with_stopwords():
    grams = keywords.ngrams_of("Candidate selection, in dominant parties.")
    assert "candidate selection" in grams and "dominant party" in grams
    assert "selection dominant" not in grams
    assert not any(g.startswith("in ") for g in grams)


def test_keyword_candidates_flag_unigrams_and_fragments():
    text = "party system nationalization matters. party system nationalization grows. " * 5
    rows = keywords.keyword_candidates([text], [])
    flags = {r["keyword"]: r["flag"] for r in rows}
    assert flags["nationalization"] == "generic_unigram"
    assert flags["party system"].startswith("fragment_of:")
    assert flags["party system nationalization"] == ""


def test_seed_rows_accept_template_and_zotero_export(tmp_path):
    template = tmp_path / "a.csv"
    template.write_text("reference,doi\n\"Smith (2020) Title. https://doi.org/10.1177/AB12\",\n,10.2307/cd\n",
                        encoding="utf-8")
    rows = seeds.read_seed_rows(template)
    assert [r["doi"] for r in rows] == ["10.1177/ab12", "10.2307/cd"]
    zotero = tmp_path / "b.csv"
    zotero.write_text('"Key","Publication Year","Author","Title","DOI"\n"K1","2019","Batto, N","Cleavage structure",""\n',
                      encoding="utf-8-sig")
    rows = seeds.read_seed_rows(zotero)
    assert rows[0]["reference"] == "Batto, N (2019) Cleavage structure"
    assert seeds.read_seed_rows(tmp_path / "missing.csv") == []


def test_dedupe_seeds_by_doi_and_text():
    items = [{"reference": "A (2020) T.", "doi": "10.1/a"}, {"reference": "other text", "doi": "10.1/a"},
             {"reference": "Same  Text", "doi": ""}, {"reference": "same text", "doi": ""}]
    assert len(seeds.dedupe_seeds(items)) == 2


def test_clean_query_removes_ampersand():
    assert clean_query("Research & Politics: (2014)") == "Research Politics 2014"


def test_parse_item_flattens_crossref_work():
    item = {"DOI": "10.1/ABC", "title": ["Main <i>title</i>"], "subtitle": ["Sub"], "container-title": ["J"],
            "issued": {"date-parts": [[2020, 5]]}, "author": [{"family": "Van der Meer", "given": "T."}],
            "abstract": "<jats:p>Abstract text here.</jats:p>", "type": "journal-article",
            "reference": [{"DOI": "10.2/X"}, {"author": "Sartori", "year": "1976", "volume-title": "Parties"}],
            "references-count": 2}
    record = parse_item(item)
    assert record["doi"] == "10.1/abc" and record["title"] == "Main title: Sub" and record["year"] == "2020"
    assert record["authors_str"] == "Van der Meer, T."
    assert record["abstract"] == "text here." or record["abstract"] == "Abstract text here."
    assert record["references"] == [{"doi": "10.2/x"}, {"author": "Sartori", "year": "1976", "volume_title": "Parties"}]


def test_consistent_match_rejects_wrong_author_or_type():
    review = {"authors": [{"family": "Grynaviski", "given": "J"}], "editors": [], "type": "journal-article"}
    book = {"authors": [{"family": "Chhibber", "given": "P"}], "editors": [], "type": "monograph"}
    assert not consistent_match(review, "Chhibber P", True)
    assert consistent_match(book, "Chhibber P", True)
    assert not consistent_match({**book, "type": "journal-article"}, "Chhibber P", True)
