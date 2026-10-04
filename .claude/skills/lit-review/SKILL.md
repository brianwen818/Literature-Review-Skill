---
name: lit-review
description: Collect relevant journal articles for a literature review. Starting from the user's main documents (manuscript or key papers) and seed references, search a chosen list of journals through Crossref, score every hit, read the best ones, and deliver two Excel workbooks plus a summary; after the user marks which articles to keep, add them to Zotero or export them. Use when the user asks to find, collect, expand or screen literature for a paper, or mentions seed references, journal lists, or adding search results to Zotero.
---

# Literature review collection

You run a pipeline of scripts and do the judgment work between them. The scripts
are deterministic; the parts marked **You** are where your reading matters.

All commands run from the repository root. `P` below stands for the project
selector: `--project NAME` (a folder under `projects/`) or `--project-dir PATH`.
Every script has `--help`.

## Before you start

- Install dependencies once: `pip install -r requirements.txt`.
- Talk to the user in the language they use. Paths, column names and script
  output stay as they are.
- Never open, print or copy `inputs/zotero-info/.env`. The scripts read it themselves.
- Everything under `projects/` is the user's private data and is not committed.

## What the user provides

| Input | Where | Required |
|---|---|---|
| Main documents: the manuscript and/or key papers (PDF, `.md`, `.txt`) | `inputs/main-docs/` | yes, at least one |
| Seed references: citations or DOIs, or a Zotero CSV export | `inputs/seed-references.csv` | no; falls back to the main documents' reference lists |
| Journals to search | `inputs/journal-lists.csv` | yes, but you may propose them |
| Settings: n, shortlist mode, years, library link | `inputs/config.yaml` | defaults exist |
| Zotero credentials | `inputs/zotero-info/.env` | only for uploading |

Ask for `n` (how many articles), the journals, the shortlist mode (`global` =
best n overall, `per-journal` = n/m from each journal) and a year range if the
user has not said. Write the answers into `config.yaml`.

## Steps

### 1. Create the project
```
python codes/scripts/01_init_project.py P
```
Then have the user put their files in `inputs/` (or do it for them if they point you to the files).

### 2. Main documents
```
python codes/scripts/02_prepare_main_docs.py P
```
Check the printed notes. `low_text_per_page` means a scanned PDF: tell the user it needs OCR.
Read the converted documents in `intermediate-data/processed-main-docs/` yourself — you
need to understand the research question to judge relevance later.

### 3. Seed references
```
python codes/scripts/03_prepare_seeds.py P
```
Open `intermediate-data/processed-seed-references.csv`. A reference is accepted only when
the Crossref score, title, first author and year all agree; the rest are `low_confidence`
with the failing checks listed in `failed_checks`.

**You:** look at the `low_confidence` rows that have a plausible `matched_title`. Accept a
row only when the candidate is the cited work itself — never a review of it, a different
edition's review, or the book that contains a cited chapter:
```
python codes/scripts/03_prepare_seeds.py P --accept 4,17
```
Books, news items and non-English works usually stay unresolved. That is expected; say how
many seeds were resolved.

### 4. Journals
If `journal-lists.csv` is empty, **you** propose journals: pick from `references/journal-lists/`
(field lists with ISSNs) according to the main documents, show the list to the user, and write
the agreed rows into `inputs/journal-lists.csv`. Then:
```
python codes/scripts/04_prepare_journals.py P
```
Journals with status `needs_review` are searched unless you set `use` to `no` in
`intermediate-data/journals-validated.csv`; check that the Crossref title is the intended journal.

### 5. Keywords
```
python codes/scripts/05_extract_keywords.py P
```
**You:** edit `intermediate-data/keywords.csv` (columns `keyword, use, source, note`). The
starting list is frequency-based and needs judgment:
- Remove terms that would match most articles in these journals (too generic) or that are
  tied to the manuscript's wording rather than to the literature.
- Add concepts the argument depends on that the counts missed, including the standard terms
  other authors use for the same idea. Mark them `source = agent`.
- Prefer two- and three-word phrases. Keep within `max_keywords`.
- If the main documents are not in English, write English keywords.

Bad keywords are the main way a run goes off topic, so take this step seriously.

### 6. Checkpoint with the user, then search
```
python codes/scripts/06_search_journals.py P --plan
```
Show the user the keyword list, the journal list and the number of queries, and wait for
their confirmation. Then:
```
python codes/scripts/06_search_journals.py P            # add --zotero to skip items already in their library
```
The search resumes where it stopped if interrupted. If it reports failed queries, run it again.
`--zotero` needs credentials; use it only when the user has set them up.

### 7. SPECTER (optional)
```
python codes/scripts/07_check_specter.py P
```
Report the recommendation. Leave `use_specter: off` unless the user wants it; turning it on
requires `pip install -r requirements-specter.txt`. Ask before installing anything that large.

### 8. Score
```
python codes/scripts/08_score_candidates.py P
```
This writes reading batches to `intermediate-data/judging/search/batch-NNN.json`.

### 9. Read and judge
**You:** read every batch. For each `batch-NNN.json` write `judged-NNN.json` in the same folder:
a JSON list with one object per article:
```json
{"item_id": "10.1177/...", "relevance": 4, "reason": "one sentence", "theme": "short label"}
```
- `relevance`: 5 = central to the user's argument; 4 = directly useful; 3 = useful background;
  2 = loosely related; 1 = off topic. Judge against the user's research question, not against
  keyword overlap.
- `reason`: what the article would contribute to this manuscript. Be specific; these sentences
  go into the workbook and the summary.
- `theme`: a short label. Reuse a small set of labels (about 5–12) across all batches so the
  summary can group by them.
- Many articles have no abstract (some publishers do not deposit them). Judge those from the
  title and journal and say so only if it limits your confidence.
- For large runs, split the batches among subagents; give each the research question and this rubric.

Then:
```
python codes/scripts/09_merge_judgments.py P
```
If it reports missing items, they are listed in `todo.json`; judge them and run it again.

### 10. Snowballing
```
python codes/scripts/10_snowball.py P
```
This collects works cited by the best articles and by the seeds — the way books and articles
outside the journal list are found. **You:** judge `judging/snowball/batch-NNN.json` the same
way (items without a DOI have only a title or a raw citation), then:
```
python codes/scripts/09_merge_judgments.py P --stage snowball
```

### 11. Build the outputs
```
python codes/scripts/11_build_outputs.py P
```
- `outputs/all-relevant-articles.xlsx` — every candidate above the threshold, by journal then relevance.
- `outputs/shortlist.xlsx` — sheet `shortlist` (n articles) and sheet `snowball`; each has an
  `add-zotero-or-not` dropdown and a library search link.
- `outputs/summary.md` — the numbers are filled in.

**You:** replace the `<!-- AGENT: ... -->` comment in `summary.md` with the analysis, in the
user's language: the overall picture, which clusters matter most for this manuscript and why,
and what this search could not cover (for example books, non-English literature, journals
outside the list, topics with no hits) with concrete suggestions. Base it on what you read;
do not restate the tables.

### 12. Checkpoint: the user marks the shortlist
Tell the user to open `shortlist.xlsx`, choose yes/no in `add-zotero-or-not` on both sheets,
then save and close the file. Stop here until they say they are done.

### 13. Finalize
Ask whether to add the marked items to Zotero or only export them.
```
python codes/scripts/12_finalize.py P                      # export only: zotero-added.xlsx + zotero-import.ris
python codes/scripts/12_finalize.py P --upload --dry-run   # show what would be added
python codes/scripts/12_finalize.py P --upload             # add to Zotero, then zotero-added.xlsx + zotero-export.rdf
```
Uploading writes to the user's library: run `--upload` only when they asked for it, and show
the `--dry-run` result first. Records only, no PDFs. Items already in the library are skipped,
and each batch gets a dated tag so it can be found and removed.

## If something changes midway

- New seeds or main documents: re-run from step 2 or 3. Seed lookups are cached.
- New keywords or journals: re-run step 6; only the new queries are sent.
- After re-running step 8 or 10, earlier judgments are kept; only new items need judging.
- `11_build_outputs.py` refuses to overwrite a shortlist that already has marks unless `--force` is given.

## Limits to tell the user about

- Crossref has almost no Chinese-language scholarship and incomplete abstracts.
- The journal search returns journal articles only; books surface through snowballing, and
  only when several relevant articles cite them.
- Scores rank candidates within this run; they are not comparable across runs.
