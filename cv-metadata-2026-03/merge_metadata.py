#!/usr/bin/env python3
"""
Merge alchemical dataset metadata from multiple sources into one master CSV.

Sources:
  1. CHR2023-corpus-train.csv (18 rows) — training split
  2. CHR2023-corpus-eval.csv (7 rows) — evaluation split
  3. 2024-09-25_hab-dataset-img-metadata.csv (73 rows) — HAB library originals
  4. hab_scraped_metadata.csv (73 rows) — scraped from HAB TEI XML
  5. ChatGPT-normalized file with inferred normalizations and likely-identical groupings
  6. Manual corrections for 4 previously-incomplete entries

Pipeline:
  original -> scraped (HAB TEI XML) -> resolved (best available) -> normalized
  -> inferred (ChatGPT suggestions) -> likely_identical (cross-entry groupings)
"""

import pandas as pd
import re

# ============================================================
# 1. READ ALL SOURCES
# ============================================================

train = pd.read_csv("/Users/slang/Downloads/CHR2023-corpus-train.csv", keep_default_na=False)
eval_ = pd.read_csv("/Users/slang/Downloads/CHR2023-corpus-eval.csv", keep_default_na=False)
hab_scraped = pd.read_csv("/Users/slang/claude/hab_scraped_metadata.csv", keep_default_na=False)
chatgpt = pd.read_csv(
    "/Users/slang/Downloads/CV metadata overview sheet - historical_books_normalized_likely_identical.csv",
    keep_default_na=False
)

# ============================================================
# 2. MANUAL CORRECTIONS for previously-incomplete entries
#    (researched by the user)
# ============================================================

MANUAL_CORRECTIONS = {
    "http://diglib.hab.de/drucke/xb-1648/start.htm": {
        "long_title": "Probier Büchlein auff Gold/ Silber/ Ertz und Metall/ : mit viel köstlichen Alchimistischen Künsten/ sampt aller Zugehör/ auch Instrumenten darzu dienstlich. Mehr deß Goldfärbens besondere KunstStücklin. Item ein Erklärung der Bergknamen/ für die newen angehenden Bergkleuth. Alles mit sonderm Fleiß für die Liebhaber der Kunst beschrieben",
        "year_manual": "1608",
        "publisher_manual": "Steinmeyer",
        "place_manual": "Frankfurt am Main",
        "short_title_inferred": "Probier Büchlein (Gold und Metall)",
        "language_inferred": "German",
        "normalization_notes_inferred": "Anonymous; typical German Probierbüchlein tradition; Frankfurt imprint normalised; manually researched",
        "short_title_likely_identical_shared": "Probierbüchlein tradition",
        "publisher_likely_identical_shared": "Steinmeyer",
        "likely_identical_notes": "Likely part of the broader Probierbüchlein textual tradition",
    },
    "http://diglib.hab.de/drucke/218-9-quod-11s/start.htm": {
        "long_title": "Von allen geprenten wassern/ in welicher maß man die nützen vnd gebrauchen sol/ zu gesundtheit vnd fristung der gebrechen der menschen",
        "author_manual": "Michael Schrick",
        "year_manual": "1530",
        "publisher_manual": "Jobst Gutknecht",
        "place_manual": "Nuremberg",
        "short_title_inferred": "Von gebrannten Wassern",
        "language_inferred": "German",
        "author_normalized_inferred": "Michael Schrick",
        "publisher_normalized_inferred": "Jobst Gutknecht",
        "place_normalized_inferred": "Nuremberg",
        "normalization_notes_inferred": "Early New High German; spelling normalised; matches Schrick distillation tradition; manually researched",
        "author_likely_identical_shared": "Michael Schrick",
        "short_title_likely_identical_shared": "Von gebrannten Wassern",
        "likely_identical_notes": "Same textual tradition as other Schrick/Brunschwig distillation books",
    },
    "http://diglib.hab.de/drucke/196-quod-1s/start.htm": {
        "long_title": "Atalanta Fugiens, hoc est, Emblemata Nova De Secretis Naturae Chymica : Accommodata partim oculis & intellectui, figuris cupro incisis, adiectisque sententiis, Epigrammatis & notis, partim auribus & recreationi animi plus minus 50 Fugis Musicis",
        "author_manual": "Michael Maier",
        "year_manual": "1618",
        "publisher_manual": "de Bry",
        "place_manual": "Oppenheim",
        "short_title_inferred": "Atalanta fugiens",
        "language_inferred": "Latin",
        "author_normalized_inferred": "Michael Maier",
        "publisher_normalized_inferred": "De Bry",
        "place_normalized_inferred": "Oppenheim",
        "normalization_notes_inferred": "Canonical Latin title; place normalised (Oppenheimii -> Oppenheim); manually researched",
        "author_likely_identical_shared": "Michael Maier",
        "publisher_likely_identical_shared": "De Bry",
        "short_title_likely_identical_shared": "Atalanta fugiens",
        "likely_identical_notes": "Unique work but consistent author/publisher normalisation",
    },
    "http://diglib.hab.de/drucke/416-quod-2s/start.htm": {
        "long_title": "Probir büchlin / vff Golt Silber / Kupfer / Blei / vn\u0304 allerley ertz Gemeynem nütz zu gut geordenet. Müntzmeyſtern / Gwardeinē / Goͤldſchmiden / Goltschlahern / Müntzregirern / Bergkleutten / vnd Probirern / fast dinstlich vnd nützt. Etzlich bercknamen / den newen anfangenden berckleute dinstlich.",
        "short_title_inferred": "Probierbüchlein (Metals)",
        "language_inferred": "German",
        "normalization_notes_inferred": "Anonymous; undated print; likely 16th century; orthography preserved; manually researched",
        "short_title_likely_identical_shared": "Probierbüchlein tradition",
        "likely_identical_notes": "Grouped with other Probierbüchlein-type assay manuals",
    },
}

# ============================================================
# 3. BUILD CHR2023 ROWS (train + eval, same schema)
# ============================================================

train["source_file"] = "CHR2023-corpus-train"
train["dataset_split"] = "train"
eval_["source_file"] = "CHR2023-corpus-eval"
eval_["dataset_split"] = "eval"
chr_df = pd.concat([train, eval_], ignore_index=True)

chr_rows = []
for _, r in chr_df.iterrows():
    chr_rows.append({
        "source_id": r["filename"],
        "source_collection": "CHR2023",
        "source_file": r["source_file"],
        "dataset_split": r["dataset_split"],
        "short_title": r["shorttitle"],
        "long_title": r["longtitle"],
        "bibliographic_description": "",
        "author_original": r["author"],
        "author_scraped": "",
        "year_original": str(r["date"]) if r["date"] != "" else "",
        "year_scraped": "",
        "publisher_original": r["publisher"],
        "publisher_scraped": "",
        "place_original": r["pubplace"],
        "place_scraped": "",
        "language_original": r["Sprache"],
        "url": r["url"],
        "signature": "",
        "signature_link": "",
        "scraped_ppn": "",
        "scrape_status": "",
        "page_numbers_included": "",
        "pdf_total_pages": str(r["PDFpages"]) if r["PDFpages"] != "" else "",
        "comments": r["comments"],
    })

# ============================================================
# 4. BUILD HAB ROWS (original + scraped merged side by side)
# ============================================================

hab_rows = []
for _, r in hab_scraped.iterrows():
    orig_author = r.get("author", "")
    orig_title = r.get("title", "")
    orig_place = r.get("publishing_place", "")
    orig_publisher = r.get("publisher", "")
    orig_year = str(r.get("publication_year", "")) if r.get("publication_year", "") != "" else ""
    url = r["signature_link"]

    # Check for manual corrections
    manual = MANUAL_CORRECTIONS.get(url.strip(), {})

    hab_rows.append({
        "source_id": r["signature"],
        "source_collection": "HAB",
        "source_file": "hab-dataset-img-metadata",
        "dataset_split": "",
        "short_title": "",
        "long_title": manual.get("long_title") or r.get("scraped_title", "") or orig_title,
        "bibliographic_description": r.get("bibliographic_description", ""),
        "author_original": orig_author,
        "author_scraped": r.get("scraped_author", ""),
        "author_manual": manual.get("author_manual", ""),
        "year_original": orig_year,
        "year_scraped": r.get("scraped_year", ""),
        "year_manual": manual.get("year_manual", ""),
        "publisher_original": orig_publisher,
        "publisher_scraped": r.get("scraped_publisher", ""),
        "publisher_manual": manual.get("publisher_manual", ""),
        "place_original": orig_place,
        "place_scraped": r.get("scraped_place", ""),
        "place_manual": manual.get("place_manual", ""),
        "language_original": "",
        "url": url,
        "signature": r["signature"],
        "signature_link": r["signature_link"],
        "scraped_ppn": r.get("scraped_ppn", ""),
        "scrape_status": r.get("scrape_status", ""),
        "page_numbers_included": r.get("page_numbers_included", ""),
        "pdf_total_pages": "",
        "comments": "",
    })

# ============================================================
# 5. COMBINE INTO MASTER
# ============================================================

# Ensure CHR rows also have manual columns
for row in chr_rows:
    row.setdefault("author_manual", "")
    row.setdefault("year_manual", "")
    row.setdefault("publisher_manual", "")
    row.setdefault("place_manual", "")

master = pd.DataFrame(chr_rows + hab_rows)
master = master.fillna("")

# ============================================================
# 6. RESOLVED COLUMNS (best available: manual > scraped > original)
# ============================================================

def resolve(original, scraped, manual=""):
    """Pick best available value: manual > scraped > original."""
    m = str(manual).strip() if manual else ""
    s = str(scraped).strip() if scraped else ""
    o = str(original).strip() if original else ""
    val = m if m else (s if s else o)
    val = re.sub(r'\s*;\s*\[u\.?\s*a\.?\]', '', val)
    return val.strip()

master["author_resolved"] = master.apply(
    lambda r: resolve(r["author_original"], r["author_scraped"], r.get("author_manual", "")), axis=1)
master["year_resolved"] = master.apply(
    lambda r: resolve(r["year_original"], r["year_scraped"], r.get("year_manual", "")), axis=1)
master["publisher_resolved"] = master.apply(
    lambda r: resolve(r["publisher_original"], r["publisher_scraped"], r.get("publisher_manual", "")), axis=1)
master["place_resolved"] = master.apply(
    lambda r: resolve(r["place_original"], r["place_scraped"], r.get("place_manual", "")), axis=1)

# ============================================================
# 7. NORMALIZATIONS (applied to resolved columns)
# ============================================================

def normalize_author(name):
    if not name or str(name).strip() == "":
        return ""
    name = str(name).strip()
    name = name.replace("Ã¦", "ae")
    name = re.sub(r'<<([^>]+)>>', r'\1', name)
    name = re.sub(r'<([^>]+)>', r'\1', name)
    has_et_al = bool(re.search(r'\[u\.\s*a\.\]', name))
    name = re.sub(r'\s*\[u\.\s*a\.\]', '', name)
    authors = re.split(r'\s*[;&]\s*', name)
    normalized = []
    for a in authors:
        a = a.strip()
        if not a:
            continue
        if "," in a:
            parts = [p.strip() for p in a.split(",", 1)]
            if len(parts) == 2 and parts[1]:
                a = f"{parts[1]} {parts[0]}"
            else:
                a = parts[0]
        a = re.sub(r'\s+', ' ', a).strip()
        a = re.sub(r'\s*\([^)]*\)\s*$', '', a).strip()
        normalized.append(a)
    result = "; ".join(normalized)
    if has_et_al:
        result += " et al."
    return result

master["author_normalized"] = master["author_resolved"].apply(normalize_author)

PLACE_MAP = {
    "london": "London", "franckfurt": "Frankfurt am Main",
    "franckfurt a. m.": "Frankfurt am Main", "franckfurt am mayn": "Frankfurt am Main",
    "franckfurt am main": "Frankfurt am Main", "frankfurt am main": "Frankfurt am Main",
    "franckfort": "Frankfurt am Main", "franckenfurt, am meyn": "Frankfurt am Main",
    "franckenfurt am meyn": "Frankfurt am Main", "frankfurt am mayn": "Frankfurt am Main",
    "francofurti": "Frankfurt am Main", "francofurti ad moenum": "Frankfurt am Main",
    "franckfurt am mäyn": "Frankfurt am Main", "franckfuhrt": "Frankfurt am Main",
    "franckfurdt am mayn": "Frankfurt am Main", "franckfort am mayn": "Frankfurt am Main",
    "frankfurt/main": "Frankfurt am Main", "frankfurt / main": "Frankfurt am Main",
    "münchen": "Munich", "munich": "Munich",
    "straßburg": "Strasbourg", "strasbourg": "Strasbourg", "argentorati": "Strasbourg",
    "basel": "Basel", "basileae": "Basel", "basilea": "Basel",
    "romae": "Rome", "rome": "Rome",
    "lugduni": "Lyon", "lugduni batavorum": "Leiden", "lyon": "Lyon",
    "amstelodami": "Amsterdam", "amsterdam": "Amsterdam",
    "berlini": "Berlin", "berlin": "Berlin",
    "vinegia": "Venice", "venetia": "Venice", "venetiis": "Venice", "venice": "Venice",
    "bononiae": "Bologna", "bologna": "Bologna",
    "paris": "Paris", "parisiis": "Paris",
    "leyden": "Leiden", "leiden": "Leiden",
    "zellerfeldt": "Zellerfeld", "ravennae": "Ravenna",
    "zürich": "Zurich", "zurich": "Zurich",
    "coloniæ": "Cologne", "coloniae": "Cologne", "köln": "Cologne", "cologne": "Cologne",
    "genevae": "Geneva", "genf": "Geneva",
    "hamburg": "Hamburg", "hambvrgi": "Hamburg",
    "norimbergae": "Nuremberg", "nürnberg": "Nuremberg", "nuremberg": "Nuremberg",
    "lipsiae": "Leipzig", "leipzig": "Leipzig", "lejpzjg": "Leipzig",
    "wittenberg": "Wittenberg", "wittenbergae": "Wittenberg",
    "erfurt": "Erfurt", "erfurti": "Erfurt",
    "marburg": "Marburg", "marburgi": "Marburg", "marpurgi": "Marburg",
    "hannover": "Hanover", "hannoverae": "Hanover",
    "ursellis": "Oberursel",
    "lubecae": "Lübeck", "lubeck": "Lübeck", "lübeck": "Lübeck",
    "gedani": "Gdańsk", "gedanum": "Gdańsk", "danzig": "Gdańsk",
    "oppenheim": "Oppenheim", "oppenheimio": "Oppenheim",
    "ienae": "Jena", "jena": "Jena",
    "helmstadii": "Helmstedt", "helmstedt": "Helmstedt",
    "halae": "Halle", "halle": "Halle", "hall in sachsen": "Halle",
    "goudae": "Gouda", "gouda": "Gouda",
    "wienn": "Vienna", "wien": "Vienna", "vienna": "Vienna",
    "breslau": "Wrocław", "wroclaw": "Wrocław",
    "augsburg": "Augsburg", "arnstadt": "Arnstadt",
    "s.l.": "",
}

def normalize_place(place):
    if not place or str(place).strip() == "":
        return ""
    place = str(place).strip()
    place = re.sub(r'\s*;\s*\[u\.?\s*a\.?\]', '', place).strip()
    place = re.sub(r'^\[(.+)\]$', r'\1', place.strip())
    key_full = place.lower().strip()
    if key_full in PLACE_MAP:
        return PLACE_MAP[key_full]
    if " / " in place:
        parts = [p.strip() for p in place.split("/")]
        for p in reversed(parts):
            key = p.lower().strip()
            if key in PLACE_MAP:
                return PLACE_MAP[key]
        return parts[-1].strip()
    if ";" in place:
        parts = [p.strip() for p in place.split(";") if p.strip()]
        place = parts[0]
    key = place.lower().strip()
    if key in PLACE_MAP:
        return PLACE_MAP[key]
    key_clean = key.rstrip(".,;: ")
    if key_clean in PLACE_MAP:
        return PLACE_MAP[key_clean]
    return place.strip()

master["place_normalized"] = master["place_resolved"].apply(normalize_place)

def normalize_publisher(pub):
    if not pub or str(pub).strip() == "":
        return ""
    pub = str(pub).strip()
    pub = pub.replace("Ã¦", "ae")
    pub = re.sub(r'\s*;\s*\[u\.?\s*a\.?\]', '', pub)
    pub = pub.rstrip(".,;:")
    pub = re.sub(r'\s+', ' ', pub).strip()
    return pub

master["publisher_normalized"] = master["publisher_resolved"].apply(normalize_publisher)

def normalize_year(y):
    if not y or str(y).strip() == "":
        return ""
    y = str(y).strip()
    match = re.search(r'(\d{4})', y)
    if match:
        return int(match.group(1))
    return ""

master["year_normalized"] = master["year_resolved"].apply(normalize_year)

def get_decade(year):
    if isinstance(year, (int, float)) and year != "" and year == year:
        return f"{(int(year) // 10) * 10}s"
    return ""

def get_century(year):
    if isinstance(year, (int, float)) and year != "" and year == year:
        c = (int(year) - 1) // 100 + 1
        return f"{c}th c."
    return ""

master["decade"] = master["year_normalized"].apply(get_decade)
master["century"] = master["year_normalized"].apply(get_century)

LANG_MAP = {"DE": "German", "EN": "English", "LAT": "Latin", "IT": "Italian", "FR": "French"}

def normalize_language(lang):
    if not lang or str(lang).strip() == "":
        return ""
    return LANG_MAP.get(str(lang).strip().upper(), str(lang).strip())

master["language_normalized"] = master["language_original"].apply(normalize_language)

def count_pages(pages_str):
    if not pages_str or str(pages_str).strip() == "":
        return ""
    parts = [p.strip() for p in str(pages_str).split(",") if p.strip()]
    return len(parts)

master["pages_included_count"] = master["page_numbers_included"].apply(count_pages)

def completeness_flag(row):
    key_fields = ["author_resolved", "year_resolved", "publisher_resolved", "place_resolved"]
    empty_values = {"", "[S.l.]", "[s.l.]"}
    filled = sum(1 for f in key_fields if str(row.get(f, "")).strip() not in empty_values)
    if filled == 4:
        return "complete"
    elif filled >= 2:
        return "partial"
    else:
        return "minimal"

master["metadata_completeness"] = master.apply(completeness_flag, axis=1)

# ============================================================
# 8. JOIN ChatGPT NORMALIZATIONS
# ============================================================

# Build URL-keyed lookup from ChatGPT file, skipping empty/duplicate rows
chatgpt_lookup = {}
for _, r in chatgpt.iterrows():
    url = str(r.get("url", "")).strip()
    if not url:
        continue
    # Skip rows with empty main fields (duplicates at end of file)
    if not r.get("long_title", "").strip() and not r.get("author_normalized_inferred", "").strip():
        # But keep if it has normalization_notes_inferred
        if not r.get("normalization_notes_inferred", "").strip():
            continue
    chatgpt_lookup[url] = r

# New columns from ChatGPT
chatgpt_cols = [
    "author_normalized_inferred",
    "publisher_normalized_inferred",
    "place_normalized_inferred",
    "short_title_inferred",
    "language_inferred",
    "normalization_notes_inferred",
    "author_likely_identical_shared",
    "publisher_likely_identical_shared",
    "short_title_likely_identical_shared",
    "likely_identical_notes",
]

for col in chatgpt_cols:
    master[col] = ""

for idx, row in master.iterrows():
    url = str(row.get("url", "")).strip()
    if url in chatgpt_lookup:
        cgpt = chatgpt_lookup[url]
        for col in chatgpt_cols:
            val = str(cgpt.get(col, "")).strip()
            if val:
                master.at[idx, col] = val

    # Also apply manual correction overrides for ChatGPT columns
    manual = MANUAL_CORRECTIONS.get(url, {})
    for col in chatgpt_cols:
        if col in manual and manual[col]:
            master.at[idx, col] = manual[col]

# Fill language_inferred into language_normalized where missing
for idx, row in master.iterrows():
    if not str(row.get("language_normalized", "")).strip():
        lang_inf = str(row.get("language_inferred", "")).strip()
        if lang_inf:
            master.at[idx, "language_normalized"] = lang_inf

# Fill short_title_inferred into short_title where missing
for idx, row in master.iterrows():
    if not str(row.get("short_title", "")).strip():
        st_inf = str(row.get("short_title_inferred", "")).strip()
        if st_inf:
            master.at[idx, "short_title"] = st_inf

# ============================================================
# 9. FINAL COLUMN ORDER
# ============================================================

final_cols = [
    # Identity & source tracking
    "source_id",
    "source_collection",
    "source_file",
    "dataset_split",

    # Titles
    "short_title",
    "short_title_inferred",
    "long_title",
    "bibliographic_description",

    # Author pipeline: original -> scraped -> manual -> resolved -> normalized -> inferred -> likely_identical
    "author_original",
    "author_scraped",
    "author_manual",
    "author_resolved",
    "author_normalized",
    "author_normalized_inferred",
    "author_likely_identical_shared",

    # Year pipeline
    "year_original",
    "year_scraped",
    "year_manual",
    "year_resolved",
    "year_normalized",
    "decade",
    "century",

    # Publisher pipeline
    "publisher_original",
    "publisher_scraped",
    "publisher_manual",
    "publisher_resolved",
    "publisher_normalized",
    "publisher_normalized_inferred",
    "publisher_likely_identical_shared",

    # Place pipeline
    "place_original",
    "place_scraped",
    "place_manual",
    "place_resolved",
    "place_normalized",
    "place_normalized_inferred",

    # Language
    "language_original",
    "language_normalized",
    "language_inferred",

    # Grouping / likely identical
    "short_title_likely_identical_shared",
    "likely_identical_notes",

    # Normalization notes
    "normalization_notes_inferred",

    # URLs & identifiers
    "url",
    "signature",
    "signature_link",
    "scraped_ppn",
    "scrape_status",

    # Page tracking
    "page_numbers_included",
    "pages_included_count",
    "pdf_total_pages",

    # Notes & quality
    "comments",
    "metadata_completeness",
]

master = master[final_cols]

# Sort by year then author
master = master.sort_values(
    by=["year_normalized", "author_normalized"],
    key=lambda col: col.apply(lambda x: x if x != "" else "zzz"),
    na_position="last"
).reset_index(drop=True)

# ============================================================
# 10. OUTPUT
# ============================================================

output_path = "/Users/slang/claude/master_metadata.csv"
master.to_csv(output_path, index=False, encoding="utf-8-sig")

print(f"Master metadata written to: {output_path}")
print(f"Total rows: {len(master)}")
print(f"  CHR2023 train: {len(train)}")
print(f"  CHR2023 eval:  {len(eval_)}")
print(f"  HAB:           {len(hab_scraped)}")
print(f"  ChatGPT normalizations joined: {sum(1 for u in master['url'] if u.strip() in chatgpt_lookup)}")
print(f"  Manual corrections applied: {sum(1 for u in master['url'] if u.strip() in MANUAL_CORRECTIONS)}")

print(f"\nMetadata completeness (using resolved fields):")
print(master["metadata_completeness"].value_counts().to_string())

print(f"\nColumns ({len(master.columns)}):")
for c in master.columns:
    non_empty = (master[c].astype(str).str.strip() != "").sum()
    print(f"  {c}: {non_empty}/{len(master)} filled")
