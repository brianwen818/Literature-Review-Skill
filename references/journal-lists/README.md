# Journal lists by field

Ranked journal lists that can be used as a starting point for `inputs/journal-lists.csv`.
Copy the rows you want into your project's `journal-lists.csv` (the first three columns match).

A missing ISSN is fine: step 4 (`04_prepare_journals.py`) looks the journal up in Crossref by its title.
Crossref covers few Chinese- and Russian-language journals, so most entries in the
`mainland_china_social_science` and `russia_social_science` lists will come back as `not_found`.

These lists reflect one research group's reading of each field as of August 2026; treat the ranking as a
suggestion, not as an authoritative ranking.

| File | Journals | With ISSN |
|---|---|---|
| [central_asian_studies.csv](central_asian_studies.csv) | 35 | 25 |
| [diplomacy.csv](diplomacy.csv) | 40 | 3 |
| [east_asian_studies.csv](east_asian_studies.csv) | 60 | 27 |
| [economics.csv](economics.csv) | 60 | 19 |
| [finance_quant.csv](finance_quant.csv) | 20 | 20 |
| [international_development.csv](international_development.csv) | 50 | 8 |
| [international_relations.csv](international_relations.csv) | 50 | 17 |
| [mainland_china_social_science.csv](mainland_china_social_science.csv) | 50 | 0 |
| [methodology.csv](methodology.csv) | 50 | 7 |
| [organization_theory.csv](organization_theory.csv) | 50 | 25 |
| [political_economy.csv](political_economy.csv) | 50 | 22 |
| [political_science.csv](political_science.csv) | 60 | 29 |
| [public_administration.csv](public_administration.csv) | 50 | 22 |
| [public_policy.csv](public_policy.csv) | 50 | 14 |
| [russia_social_science.csv](russia_social_science.csv) | 50 | 0 |
| [sociology.csv](sociology.csv) | 60 | 28 |
