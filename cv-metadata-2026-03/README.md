# Alchemical Laboratory Objects Dataset -- Source Book Metadata

Merged and normalized bibliographic metadata for a computer vision / object detection dataset of alchemical laboratory objects depicted in early modern printed books (ca. 1500--1750).

## What this is

The dataset images come from digitized pages of books on alchemy, distillation, metallurgy, and related arts. This repository contains **metadata about the 98 source books**, not the images or object annotations themselves. The metadata is intended to support visualizations and analysis such as:

- Which types of objects appear in which books or time periods?
- How does the visual representation of laboratory equipment change over time?
- Geographic and temporal distribution of the source material

## How this metadata was created

This metadata was assembled through a multi-step, multi-tool process combining automated scraping, manual research, and AI-assisted normalization:

1. **Three original metadata files** were provided with different schemas and varying levels of completeness:
   - `CHR2023-corpus-train.csv` (18 books) and `CHR2023-corpus-eval.csv` (7 books) -- from a 2023 CHR (Computational Humanities Research) corpus, with full bibliographic metadata and German-language comments about illustration content
   - `2024-09-25_hab-dataset-img-metadata.csv` (73 books) -- from the Herzog August Bibliothek (HAB) Wolfenbuettel, initially with mostly just library signatures and page numbers (only ~11 of 73 entries had any bibliographic metadata, and that metadata had systematic parsing errors)

2. **Automated scraping** (March 2026): A Python script (`scrape_hab_metadata.py`) fetched TEI XML metadata from the HAB digital library (`diglib.hab.de`) for all 73 HAB entries. This recovered structured metadata (author, title, publisher, place, year, PPN catalog identifier) for 69 of 73 entries directly from the library's catalog records.

3. **Manual research** (March 2026): Four entries that had neither original metadata nor accessible TEI XML were manually researched using library catalogs and secondary sources. These include Michael Maier's *Atalanta Fugiens* (1618), Michael Schrick's *Von gebrannten Wassern* (1530), and two anonymous *Probierbüchlein* (assay manuals).

4. **AI-assisted normalization** (March 2026): ChatGPT (GPT-5.3, March 2026) was used to:
   - Suggest improved author normalizations (e.g., identifying that "Paracelsus" and "Philippus Theophrastus Bombast von Hohenheim" refer to the same person)
   - Infer short titles for all entries
   - Infer publication languages for HAB entries (which lacked this field)
   - Identify "likely identical" groupings -- entries that represent different editions/translations of the same work (e.g., five editions of Biringuccio's *Pirotechnia*)
   - Flag entries where the author attribution is uncertain or pseudepigraphic (e.g., "Pseudo-Geber", "Pseudo-Lull")
   - Add normalization notes explaining what was changed and why

5. **Automated merging** (March 2026): A Python script (`merge_metadata.py`, developed with Claude Code / Claude Opus) combined all sources into a single master table with a traceable pipeline: `original` -> `scraped` -> `manual` -> `resolved` -> `normalized` -> `inferred` -> `likely_identical`. All original values are preserved in separate columns so that every normalization can be verified.

## Output: `master_metadata.csv`

98 rows, 51 columns, sorted by publication year.

### Coverage summary

| Metric | Count |
|--------|-------|
| Total books | 98 |
| Complete metadata (author + year + publisher + place) | 87 |
| Partial metadata (2--3 of 4 key fields) | 10 |
| Minimal metadata (anonymous and/or undated) | 1 |
| Date range | 1509--1751 |
| Unique normalized places | 29 cities |
| Languages | German (39), Latin (32), German+Latin (10), uncertain (7), Italian (5), French (4), English (1) |
| Likely-identical work groupings | 17 groups covering 45 entries |

### Column reference

#### Identity and provenance

| Column | Description | Example |
|--------|-------------|---------|
| `source_id` | Unique identifier within its source collection | `Brunschwig1527-DistillationEN` or `nd-4f-18` |
| `source_collection` | `CHR2023` or `HAB` |  |
| `source_file` | Specific input file | `CHR2023-corpus-train` |
| `dataset_split` | Train/eval split (CHR2023 only) | `train`, `eval`, or empty |

#### Titles

| Column | Description |
|--------|-------------|
| `short_title` | Abbreviated title (from CHR2023 or inferred by ChatGPT) |
| `short_title_inferred` | Short title suggested by ChatGPT |
| `long_title` | Full title as on the title page |
| `bibliographic_description` | Full citation string (HAB only, where available in original CSV) |

#### Author (7-stage pipeline)

| Column | Source | Description |
|--------|--------|-------------|
| `author_original` | Source CSV | Author as given in the original metadata file |
| `author_scraped` | HAB TEI XML | Author from the library's catalog record |
| `author_manual` | Manual research | Author filled in by manual research (4 entries) |
| `author_resolved` | Automated | Best available: `manual` > `scraped` > `original` |
| `author_normalized` | Automated | Resolved value with "Last, First" flipped to "First Last", etc. |
| `author_normalized_inferred` | ChatGPT | Improved normalization (e.g., canonical name forms, pseudepigrapha flagged) |
| `author_likely_identical_shared` | ChatGPT | Canonical name when multiple entries use variant spellings for the same person |

**Author normalization notes:**
- `author_normalized` applies mechanical rules: flip "Last, First" to "First Last", expand `[u.a.]` to "et al.", strip parentheticals
- `author_normalized_inferred` applies scholarly judgment: identifies that "Paracelsus" = "Philippus Theophrastus Bombast von Hohenheim", flags pseudepigraphic attributions like "Pseudo-Geber (trad. Gabir ibn Hayyan)"
- `author_likely_identical_shared` provides a single canonical form for grouping (e.g., both "Athanasius Kircher" and "Athanasius Kircherus" map to "Athanasius Kircher")

#### Year and derived temporal fields

| Column | Source | Description |
|--------|--------|-------------|
| `year_original` | Source CSV | Year as in source file |
| `year_scraped` | HAB TEI XML | Year from catalog record |
| `year_manual` | Manual research | Year from manual research |
| `year_resolved` | Automated | Best available value |
| `year_normalized` | Automated | Clean integer |
| `decade` | Derived | e.g., `1600s` |
| `century` | Derived | e.g., `17th c.` |

#### Publisher (7-stage pipeline)

| Column | Source | Description |
|--------|--------|-------------|
| `publisher_original` | Source CSV | Publisher as in source (**broken for HAB** -- see Known issues) |
| `publisher_scraped` | HAB TEI XML | Publisher from catalog record |
| `publisher_manual` | Manual research | Publisher from manual research |
| `publisher_resolved` | Automated | Best available |
| `publisher_normalized` | Automated | Trimmed, encoding-fixed |
| `publisher_normalized_inferred` | ChatGPT | Improved normalization (e.g., `Kopffius` -> `Nikolaus Kopf`) |
| `publisher_likely_identical_shared` | ChatGPT | Canonical form for grouping (e.g., `Christian Egenolff / Egenolff heirs`) |

#### Place (6-stage pipeline)

| Column | Source | Description |
|--------|--------|-------------|
| `place_original` | Source CSV | Place as in source |
| `place_scraped` | HAB TEI XML | Place from catalog record (often Latin) |
| `place_manual` | Manual research | Place from manual research |
| `place_resolved` | Automated | Best available |
| `place_normalized` | Automated | Mapped to modern English city name via ~90-entry lookup table |
| `place_normalized_inferred` | ChatGPT | ChatGPT's place normalization (sometimes includes historical/modern pair) |

#### Language

| Column | Source | Description |
|--------|--------|-------------|
| `language_original` | CHR2023 CSV | Language code (`DE`, `EN`, `LAT`, `IT`) -- CHR2023 only |
| `language_normalized` | Automated + ChatGPT | Full language name; uses `language_inferred` where `language_original` is missing |
| `language_inferred` | ChatGPT | Language inferred from title/content analysis |

#### Cross-entry groupings ("likely identical" works)

| Column | Source | Description |
|--------|--------|-------------|
| `short_title_likely_identical_shared` | ChatGPT | Canonical short title for grouping related editions/translations |
| `likely_identical_notes` | ChatGPT | Explanation of the grouping |
| `normalization_notes_inferred` | ChatGPT | Notes on what was normalized and why |

These columns enable grouping entries that represent different editions, translations, or printings of the same underlying work. For example, all five editions of Biringuccio's *Pirotechnia* (1550--1678, in Italian and French) share `short_title_likely_identical_shared` = "Pirotechnia".

17 such groups were identified, covering 45 of 98 entries.

#### URLs and identifiers

| Column | Description |
|--------|-------------|
| `url` | Primary URL to the digitized book |
| `signature` | HAB library shelfmark |
| `signature_link` | URL to HAB digital library viewer |
| `scraped_ppn` | PPN catalog number from TEI XML (Pica Production Number, used in German library union catalogs) |
| `scrape_status` | `ok`, `no_tei_xml`, or empty |

#### Page tracking

| Column | Description |
|--------|-------------|
| `page_numbers_included` | Comma-separated page numbers included in the CV dataset (HAB only) |
| `pages_included_count` | Count of included pages |
| `pdf_total_pages` | Total pages in digitized PDF (CHR2023 only) |

#### Quality indicators

| Column | Description |
|--------|-------------|
| `comments` | Free-text notes from CHR2023 (in German), describing illustration content |
| `metadata_completeness` | `complete` / `partial` / `minimal` based on 4 key fields |

## Known issues and limitations

### Data quality

- **The original HAB CSV** had a systematic parsing error: the `publisher` column consistently contained the first word of the `title`, not the actual publisher name. This was fixed by scraping from TEI XML, but `publisher_original` still contains the erroneous values for reference.

- **Author name reconciliation is partial.** The `author_likely_identical_shared` column groups known variants (e.g., Kircher/Kircherus), but not all spelling variants have been identified. Full reconciliation would require authority file lookups (VIAF, GND).

- **Publisher deduplication is partial.** The `publisher_likely_identical_shared` column groups obvious variants (e.g., "Egenolff" / "Christian Egenolff" / "Christian Egenolffs Erben") but not all have been identified.

- **Language assignment** for HAB entries was inferred by ChatGPT from title text and may contain errors. Entries marked "uncertain" have ambiguous language (e.g., Latin title but German text).

- **TEI XML titles** sometimes contain OCR artifacts like `||` (line breaks from title-page transcription). These are preserved in `long_title` as they come from the library catalog.

### Incomplete entries

- **1 minimal entry** (`416-quod-2s`): anonymous, undated *Probierbüchlein*. Likely 16th century but no firm date could be established.
- **10 partial entries**: all have year, publisher, and place but no identified author (anonymous works or compilations).

### Scope

- Metadata describes **source books**, not individual images or annotated objects. To connect to specific images, join on `source_id`.
- CHR2023 and HAB entries are treated as **disjoint**. No deduplication across collections has been attempted (the same book could theoretically appear in both under different identifiers).
- Page numbers (`page_numbers_included`) refer to **digitized PDF pages**, not the printed pagination of the original book.

## How to re-run

```bash
# Step 1: Scrape HAB metadata (only needed once, or to refresh)
python3 scrape_hab_metadata.py

# Step 2: Merge everything into master_metadata.csv
python3 merge_metadata.py

# Step 3: Generate visualizations (25 figures in figures/)
python3 visualize_corpus.py
```

**Dependencies:** Python 3.8+, pandas, matplotlib, numpy (`pip3 install pandas matplotlib numpy`)

**Note:** Scripts use hardcoded file paths. Update the paths at the top of each script if running in a different environment.

## Visualizations

25 figures analyzing the corpus are generated by `visualize_corpus.py` and saved to `figures/`. See [`VISUALIZATIONS.md`](VISUALIZATIONS.md) for detailed documentation of each figure, including technical details, assumptions, and plain-language explanations.

Topics covered include: temporal and geographic distributions, language shifts over time, edition longevity, translation flows between languages, author–publisher relationships, author geographic reach, and per-city publishing profiles.

## Sanity check

A sanity check script (inline in the development process, not a standalone file) verified the consistency of the final CSV:

- **Year pipeline**: year → decade → century all consistent across 97 dated entries
- **Author/place/publisher resolution**: all `_resolved` values trace back to a valid source (`_manual` > `_scraped` > `_original`)
- **Metadata completeness**: recalculated and verified (1 entry corrected from "complete" to "partial" because `[S.l.]` = sine loco is not a real place)
- **No `nan` string leaks**: all 51 columns checked for residual "nan"/"None"/"null" strings
- **Normalization divergences**: 16 intentional author divergences and 24 place divergences between the automated pipeline (`_normalized`) and ChatGPT's suggestions (`_normalized_inferred`) were documented in `normalization_divergences.csv` for manual review

## Files

| File | Description |
|------|-------------|
| `README.md` | This documentation |
| `VISUALIZATIONS.md` | Detailed documentation of all 25 corpus visualizations |
| `scrape_hab_metadata.py` | Script to fetch metadata from HAB TEI XML endpoints |
| `hab_scraped_metadata.csv` | Intermediate: original HAB data + scraped fields (73 rows) |
| `merge_metadata.py` | Main merge script combining all sources |
| `master_metadata.csv` | **Final output** (98 rows, 51 columns) |
| `visualize_corpus.py` | Generates all 25 corpus visualization figures |
| `figures/` | Directory containing 25 PNG figures (generated by `visualize_corpus.py`) |
| `normalization_divergences.csv` | Intentional divergences between automated and ChatGPT normalizations (40 rows) |

### Input files (not included in this repo)

| File | Description |
|------|-------------|
| `CHR2023-corpus-train.csv` | CHR2023 training split (18 books) |
| `CHR2023-corpus-eval.csv` | CHR2023 evaluation split (7 books) |
| `2024-09-25_hab-dataset-img-metadata.csv` | HAB original metadata (73 books) |
| `CV metadata overview sheet - historical_books_normalized_likely_identical.csv` | ChatGPT-normalized metadata with inferred fields and likely-identical groupings |

## Tools used

- **Claude Code** (Claude Opus, Anthropic) -- developed the scraping and merging scripts, visualizations, and documentation
- **ChatGPT** (GPT-5.3, OpenAI, March 2026) -- author/publisher normalization, language inference, short title generation, likely-identical groupings
- **HAB Wolfenbuettel digital library** (`diglib.hab.de`) -- source of TEI XML catalog metadata
- **Manual research** -- filled in 4 entries using library catalogs and secondary sources
