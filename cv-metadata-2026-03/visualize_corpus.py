#!/usr/bin/env python3
"""
Visualizations for the alchemical laboratory objects dataset metadata.
Generates a set of figures analyzing the corpus composition.
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

# ── Config ──────────────────────────────────────────────────
OUTPUT_DIR = "/Users/slang/claude/figures"
CSV_PATH = "/Users/slang/claude/master_metadata.csv"

plt.rcParams.update({
    "figure.dpi": 150,
    "savefig.dpi": 150,
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 11,
})

PALETTE = {
    "CHR2023": "#4878CF",
    "HAB": "#D65F5F",
}

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Load data ───────────────────────────────────────────────
df = pd.read_csv(CSV_PATH, keep_default_na=False)
df["year_normalized"] = pd.to_numeric(df["year_normalized"], errors="coerce")
df["pages_included_count"] = pd.to_numeric(df["pages_included_count"], errors="coerce")

# Use author_likely_identical_shared when available, else author_normalized_inferred, else author_normalized
df["author_display"] = df["author_likely_identical_shared"].where(
    df["author_likely_identical_shared"] != "",
    df["author_normalized_inferred"].where(
        df["author_normalized_inferred"] != "",
        df["author_normalized"]
    )
)

# ════════════════════════════════════════════════════════════
# FIGURE 1: Books per decade, stacked by source collection
# ════════════════════════════════════════════════════════════

def fig_books_per_decade():
    dated = df[df["year_normalized"].notna()].copy()
    dated["decade_num"] = (dated["year_normalized"] // 10 * 10).astype(int)

    all_decades = range(
        dated["decade_num"].min(),
        dated["decade_num"].max() + 10,
        10
    )

    fig, ax = plt.subplots(figsize=(12, 5))

    for i, (coll, color) in enumerate(PALETTE.items()):
        subset = dated[dated["source_collection"] == coll]
        counts = subset["decade_num"].value_counts().reindex(all_decades, fill_value=0).sort_index()
        bottom = None
        if i > 0:
            prev = dated[dated["source_collection"] == list(PALETTE.keys())[0]]
            bottom = prev["decade_num"].value_counts().reindex(all_decades, fill_value=0).sort_index().values
        ax.bar(
            counts.index, counts.values,
            width=8, bottom=bottom,
            color=color, label=coll, edgecolor="white", linewidth=0.5,
        )

    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of books")
    ax.set_title("Books in the dataset by decade of publication")
    ax.legend()
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    ax.set_xticks(list(all_decades))
    ax.set_xticklabels([f"{d}s" for d in all_decades], rotation=45, ha="right")

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/01_books_per_decade.png", bbox_inches="tight")
    plt.close(fig)
    print("  01_books_per_decade.png")


# ════════════════════════════════════════════════════════════
# FIGURE 2: Publication places (top 15)
# ════════════════════════════════════════════════════════════

def fig_publication_places():
    places = df[df["place_normalized"] != ""].copy()
    place_counts = places["place_normalized"].value_counts()
    top = place_counts.head(15)

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = [PALETTE.get("HAB")] * len(top)
    bars = ax.barh(range(len(top)), top.values, color="#6A9BC3", edgecolor="white")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top.index)
    ax.invert_yaxis()
    ax.set_xlabel("Number of books")
    ax.set_title("Top 15 publication places")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    for bar, val in zip(bars, top.values):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=10)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/02_publication_places.png", bbox_inches="tight")
    plt.close(fig)
    print("  02_publication_places.png")


# ════════════════════════════════════════════════════════════
# FIGURE 3: Language distribution
# ════════════════════════════════════════════════════════════

def fig_languages():
    langs = df[df["language_normalized"] != ""]["language_normalized"].value_counts()

    fig, ax = plt.subplots(figsize=(7, 7))
    colors = plt.cm.Set2(range(len(langs)))
    wedges, texts, autotexts = ax.pie(
        langs.values, labels=langs.index, autopct="%1.0f%%",
        colors=colors, startangle=90, pctdistance=0.8,
    )
    for t in autotexts:
        t.set_fontsize(10)
    ax.set_title("Languages of source books")

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/03_languages.png", bbox_inches="tight")
    plt.close(fig)
    print("  03_languages.png")


# ════════════════════════════════════════════════════════════
# FIGURE 4: Most frequent authors
# ════════════════════════════════════════════════════════════

def fig_top_authors():
    authors = df[df["author_display"] != ""]["author_display"].value_counts()
    top = authors[authors >= 2]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(range(len(top)), top.values, color="#7CAE7A", edgecolor="white")
    ax.set_yticks(range(len(top)))
    ax.set_yticklabels(top.index)
    ax.invert_yaxis()
    ax.set_xlabel("Number of books in dataset")
    ax.set_title("Authors with 2+ books in the dataset")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    for bar, val in zip(bars, top.values):
        ax.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=10)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/04_top_authors.png", bbox_inches="tight")
    plt.close(fig)
    print("  04_top_authors.png")


# ════════════════════════════════════════════════════════════
# FIGURE 5: Pages included per HAB book (distribution)
# ════════════════════════════════════════════════════════════

def fig_pages_per_book():
    hab = df[(df["source_collection"] == "HAB") & (df["pages_included_count"].notna())].copy()
    counts = hab["pages_included_count"].astype(int).sort_values()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [2, 1]})

    # Left: histogram
    bins = [1, 2, 3, 5, 10, 20, 50, 110]
    ax1.hist(counts, bins=bins, color="#D4A574", edgecolor="white", linewidth=0.8)
    ax1.set_xlabel("Pages included per book")
    ax1.set_ylabel("Number of books")
    ax1.set_title("Distribution of pages per book (HAB only)")
    ax1.set_xscale("log")
    ax1.xaxis.set_major_formatter(ticker.ScalarFormatter())
    ax1.xaxis.set_ticks(bins)

    # Right: top 10 books by pages
    top = hab.nlargest(10, "pages_included_count")
    labels = top["short_title"].apply(lambda x: x[:35] + "..." if len(str(x)) > 35 else x)
    ax2.barh(range(len(top)), top["pages_included_count"].values, color="#D4A574", edgecolor="white")
    ax2.set_yticks(range(len(top)))
    ax2.set_yticklabels(labels)
    ax2.invert_yaxis()
    ax2.set_xlabel("Pages included")
    ax2.set_title("Top 10 HAB books by pages included")

    for i, val in enumerate(top["pages_included_count"].values):
        ax2.text(val + 0.5, i, str(int(val)), va="center", fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/05_pages_per_book.png", bbox_inches="tight")
    plt.close(fig)
    print("  05_pages_per_book.png")


# ════════════════════════════════════════════════════════════
# FIGURE 6: Likely-identical work groups (editions over time)
# ════════════════════════════════════════════════════════════

def fig_edition_groups():
    grouped = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    # Only groups with 2+ entries
    group_sizes = grouped["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index
    grouped = grouped[grouped["short_title_likely_identical_shared"].isin(multi)]

    # Sort groups by earliest year
    group_order = (
        grouped.groupby("short_title_likely_identical_shared")["year_normalized"]
        .min().sort_values().index
    )

    fig, ax = plt.subplots(figsize=(12, 7))
    colors = plt.cm.tab20(np.linspace(0, 1, len(group_order)))

    for i, group_name in enumerate(group_order):
        subset = grouped[grouped["short_title_likely_identical_shared"] == group_name]
        years = subset["year_normalized"].values
        label = group_name if len(group_name) <= 35 else group_name[:32] + "..."
        ax.scatter(years, [i] * len(years), color=colors[i], s=80, zorder=3, edgecolors="white", linewidth=0.5)
        if len(years) > 1:
            ax.plot([years.min(), years.max()], [i, i], color=colors[i], linewidth=1.5, alpha=0.5, zorder=2)

    ax.set_yticks(range(len(group_order)))
    ax.set_yticklabels([g if len(g) <= 40 else g[:37] + "..." for g in group_order], fontsize=9)
    ax.set_xlabel("Publication year")
    ax.set_title("Editions and translations of the same work over time")
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/06_edition_groups.png", bbox_inches="tight")
    plt.close(fig)
    print("  06_edition_groups.png")


# ════════════════════════════════════════════════════════════
# FIGURE 7: Timeline scatter (year vs. pages included, HAB)
# ════════════════════════════════════════════════════════════

def fig_timeline_scatter():
    hab = df[
        (df["source_collection"] == "HAB") &
        (df["year_normalized"].notna()) &
        (df["pages_included_count"].notna())
    ].copy()

    fig, ax = plt.subplots(figsize=(12, 6))

    scatter = ax.scatter(
        hab["year_normalized"],
        hab["pages_included_count"],
        c="#D65F5F", alpha=0.6, s=60, edgecolors="white", linewidth=0.5,
    )

    # Label outliers (top 5 by page count)
    top5 = hab.nlargest(5, "pages_included_count")
    for _, r in top5.iterrows():
        label = str(r["short_title"])[:25]
        ax.annotate(
            label,
            (r["year_normalized"], r["pages_included_count"]),
            textcoords="offset points", xytext=(8, 5),
            fontsize=8, alpha=0.8,
        )

    ax.set_xlabel("Publication year")
    ax.set_ylabel("Pages included in dataset")
    ax.set_title("HAB books: publication year vs. number of pages included")
    ax.grid(alpha=0.2)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/07_timeline_scatter.png", bbox_inches="tight")
    plt.close(fig)
    print("  07_timeline_scatter.png")


# ════════════════════════════════════════════════════════════
# FIGURE 8: Collection composition overview
# ════════════════════════════════════════════════════════════

def fig_collection_overview():
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Panel 1: Books per collection
    coll_counts = df["source_collection"].value_counts()
    axes[0].bar(coll_counts.index, coll_counts.values,
                color=[PALETTE[c] for c in coll_counts.index], edgecolor="white")
    axes[0].set_ylabel("Number of books")
    axes[0].set_title("Books per collection")
    for i, (idx, val) in enumerate(coll_counts.items()):
        axes[0].text(i, val + 0.5, str(val), ha="center", fontsize=11)

    # Panel 2: Metadata completeness
    comp = df["metadata_completeness"].value_counts().reindex(["complete", "partial", "minimal"], fill_value=0)
    colors_comp = ["#7CAE7A", "#E8C170", "#D65F5F"]
    axes[1].bar(comp.index, comp.values, color=colors_comp, edgecolor="white")
    axes[1].set_ylabel("Number of books")
    axes[1].set_title("Metadata completeness")
    for i, val in enumerate(comp.values):
        axes[1].text(i, val + 0.5, str(val), ha="center", fontsize=11)

    # Panel 3: Centuries
    centuries = df[df["century"] != ""]["century"].value_counts().sort_index()
    axes[2].bar(centuries.index, centuries.values, color="#6A9BC3", edgecolor="white")
    axes[2].set_ylabel("Number of books")
    axes[2].set_title("Books per century")
    for i, val in enumerate(centuries.values):
        axes[2].text(i, val + 0.5, str(val), ha="center", fontsize=11)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/08_collection_overview.png", bbox_inches="tight")
    plt.close(fig)
    print("  08_collection_overview.png")


# ════════════════════════════════════════════════════════════
# FIGURE 9: Place x Decade heatmap
# ════════════════════════════════════════════════════════════

def fig_place_decade_heatmap():
    dated = df[(df["year_normalized"].notna()) & (df["place_normalized"] != "")].copy()
    dated["decade_num"] = (dated["year_normalized"] // 10 * 10).astype(int)

    # Top places only
    top_places = dated["place_normalized"].value_counts().head(10).index
    dated_top = dated[dated["place_normalized"].isin(top_places)]

    cross = pd.crosstab(dated_top["place_normalized"], dated_top["decade_num"])
    # Reorder by total count
    cross = cross.loc[top_places]

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(cross.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels([f"{d}s" for d in cross.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index)

    # Annotate cells
    for i in range(len(cross.index)):
        for j in range(len(cross.columns)):
            val = cross.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=9,
                        color="white" if val > cross.values.max() * 0.6 else "black")

    ax.set_title("Books per publication place and decade (top 10 places)")
    fig.colorbar(im, ax=ax, label="Number of books", shrink=0.8)

    fig.savefig(f"{OUTPUT_DIR}/09_place_decade_heatmap.png", bbox_inches="tight")
    plt.close(fig)
    print("  09_place_decade_heatmap.png")


# ════════════════════════════════════════════════════════════
# FIGURE 10: Author × Place — where did each author publish?
# ════════════════════════════════════════════════════════════

def fig_author_place_network():
    """Heatmap showing which authors published in which cities."""
    sub = df[
        (df["author_display"] != "") &
        (df["place_normalized"] != "")
    ].copy()

    # Only authors with 2+ books
    auth_counts = sub["author_display"].value_counts()
    multi_authors = auth_counts[auth_counts >= 2].index
    sub = sub[sub["author_display"].isin(multi_authors)]

    # Top places (that these authors used)
    place_counts = sub["place_normalized"].value_counts()
    top_places = place_counts.head(12).index

    cross = pd.crosstab(sub["author_display"], sub["place_normalized"])
    # Keep only top places as columns, authors with 2+ books as rows
    cross = cross.reindex(columns=top_places, fill_value=0)
    cross = cross.loc[multi_authors]
    # Drop all-zero columns
    cross = cross.loc[:, cross.sum() > 0]

    fig, ax = plt.subplots(figsize=(12, 8))
    im = ax.imshow(cross.values, cmap="YlGnBu", aspect="auto")

    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels(cross.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index)

    for i in range(len(cross.index)):
        for j in range(len(cross.columns)):
            val = cross.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=10,
                        color="white" if val > cross.values.max() * 0.6 else "black")

    ax.set_title("Authors and their publication places (authors with 2+ books)")
    fig.colorbar(im, ax=ax, label="Number of books", shrink=0.8)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/10_author_place.png", bbox_inches="tight")
    plt.close(fig)
    print("  10_author_place.png")


# ════════════════════════════════════════════════════════════
# FIGURE 11: Publisher × Decade heatmap
# ════════════════════════════════════════════════════════════

def fig_publisher_decade():
    """Top publishers across decades."""
    sub = df[
        (df["publisher_normalized_inferred"] != "") &
        (df["year_normalized"].notna())
    ].copy()
    sub["decade_num"] = (sub["year_normalized"] // 10 * 10).astype(int)

    pub_counts = sub["publisher_normalized_inferred"].value_counts()
    top_pubs = pub_counts[pub_counts >= 2].index

    sub = sub[sub["publisher_normalized_inferred"].isin(top_pubs)]

    cross = pd.crosstab(sub["publisher_normalized_inferred"], sub["decade_num"])
    cross = cross.loc[top_pubs]

    fig, ax = plt.subplots(figsize=(14, 7))
    im = ax.imshow(cross.values, cmap="OrRd", aspect="auto")

    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels([f"{d}s" for d in cross.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index)

    for i in range(len(cross.index)):
        for j in range(len(cross.columns)):
            val = cross.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=10,
                        color="white" if val > cross.values.max() * 0.6 else "black")

    ax.set_title("Publishers active across decades (publishers with 2+ books)")
    fig.colorbar(im, ax=ax, label="Number of books", shrink=0.8)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/11_publisher_decade.png", bbox_inches="tight")
    plt.close(fig)
    print("  11_publisher_decade.png")


# ════════════════════════════════════════════════════════════
# FIGURE 12: Language shifts over time
# ════════════════════════════════════════════════════════════

def fig_language_over_time():
    """Stacked area chart of publication languages by decade."""
    sub = df[
        (df["language_normalized"] != "") &
        (df["year_normalized"].notna())
    ].copy()
    sub["decade_num"] = (sub["year_normalized"] // 10 * 10).astype(int)

    # Simplify mixed languages
    def simplify_lang(lang):
        if "German" in lang and "Latin" in lang:
            return "German + Latin"
        for l in ["German", "Latin", "Italian", "French", "English"]:
            if l in lang:
                return l
        return "Other"

    sub["lang_simple"] = sub["language_normalized"].apply(simplify_lang)

    cross = pd.crosstab(sub["decade_num"], sub["lang_simple"])
    lang_order = ["Latin", "German", "German + Latin", "Italian", "French", "English", "Other"]
    lang_order = [l for l in lang_order if l in cross.columns]
    cross = cross[lang_order]

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7", "Other": "#BAB0AC"
    }

    fig, ax = plt.subplots(figsize=(13, 6))
    bottom = np.zeros(len(cross))
    for lang in lang_order:
        vals = cross[lang].values
        ax.bar(range(len(cross)), vals, bottom=bottom,
               label=lang, color=lang_colors.get(lang, "#999"),
               edgecolor="white", linewidth=0.5, width=0.8)
        bottom += vals

    ax.set_xticks(range(len(cross)))
    ax.set_xticklabels([f"{d}s" for d in cross.index], rotation=45, ha="right")
    ax.set_xlabel("Decade")
    ax.set_ylabel("Number of books")
    ax.set_title("Publication language by decade")
    ax.legend(loc="upper left")
    ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/12_language_over_time.png", bbox_inches="tight")
    plt.close(fig)
    print("  12_language_over_time.png")


# ════════════════════════════════════════════════════════════
# FIGURE 13: Edition spread — geographic & temporal reach
# ════════════════════════════════════════════════════════════

def fig_edition_spread():
    """For each work with multiple editions, show place + year as a connected scatter
    with inline labels next to the first edition of each work."""
    sub = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna()) &
        (df["place_normalized"] != "")
    ].copy()

    group_sizes = sub["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index
    sub = sub[sub["short_title_likely_identical_shared"].isin(multi)]

    # Get all unique places, ordered by latitude-ish (south to north roughly)
    all_places = sub["place_normalized"].value_counts().index.tolist()
    place_to_y = {p: i for i, p in enumerate(all_places)}

    fig, ax = plt.subplots(figsize=(16, 9))
    colors = plt.cm.tab20(np.linspace(0, 1, len(multi)))

    # Track label positions to avoid overlap
    used_label_positions = []

    for i, work in enumerate(multi):
        ws = sub[sub["short_title_likely_identical_shared"] == work].sort_values("year_normalized")
        years = ws["year_normalized"].values
        places = [place_to_y[p] for p in ws["place_normalized"]]
        label = work if len(work) <= 35 else work[:32] + "..."

        ax.scatter(years, places, color=colors[i], s=110, zorder=3,
                   edgecolors="white", linewidth=0.6)
        if len(ws) > 1:
            ax.plot(years, places, color=colors[i], linewidth=2, alpha=0.35, zorder=2)

        # Place label near the last (latest) edition — avoids the crowded early cluster
        label_x = years[-1]
        label_y = places[-1]

        # Try offsets to avoid overlap
        offsets = [
            (14, 0), (14, -14), (14, 14), (14, -28), (14, 28),
            (-14, 0), (-14, -14), (-14, 14),
            (14, -42), (14, 42), (-14, -28), (-14, 28),
        ]
        best_offset = offsets[0]
        best_ha = "left"
        for ox, oy in offsets:
            candidate_x = label_x + ox * 0.8
            candidate_y = label_y + oy * 0.04
            conflict = False
            for (ux, uy) in used_label_positions:
                if abs(candidate_x - ux) < 20 and abs(candidate_y - uy) < 0.45:
                    conflict = True
                    break
            if not conflict:
                best_offset = (ox, oy)
                best_ha = "left" if ox > 0 else "right"
                break

        ax.annotate(
            label, (label_x, label_y),
            textcoords="offset points", xytext=best_offset,
            fontsize=8.5, fontweight="bold", color=colors[i],
            ha=best_ha, va="center",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="none", alpha=0.8),
        )
        used_label_positions.append((label_x + best_offset[0] * 0.5, label_y + best_offset[1] * 0.05))

    ax.set_yticks(range(len(all_places)))
    ax.set_yticklabels(all_places, fontsize=10)
    ax.set_xlabel("Publication year", fontsize=11)
    ax.set_title("Geographic spread of works across editions and translations", fontsize=13)
    ax.grid(axis="x", alpha=0.3)
    ax.grid(axis="y", alpha=0.15)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/13_edition_spread.png", bbox_inches="tight")
    plt.close(fig)
    print("  13_edition_spread.png")


# ════════════════════════════════════════════════════════════
# FIGURE 14: Publisher × Place — where did each publisher work?
# ════════════════════════════════════════════════════════════

def fig_publisher_place():
    """Heatmap of publishers and cities."""
    sub = df[
        (df["publisher_normalized_inferred"] != "") &
        (df["place_normalized"] != "")
    ].copy()

    pub_counts = sub["publisher_normalized_inferred"].value_counts()
    top_pubs = pub_counts[pub_counts >= 2].index
    sub = sub[sub["publisher_normalized_inferred"].isin(top_pubs)]

    cross = pd.crosstab(sub["publisher_normalized_inferred"], sub["place_normalized"])
    cross = cross.loc[top_pubs]
    # Drop zero columns
    cross = cross.loc[:, cross.sum() > 0]

    fig, ax = plt.subplots(figsize=(12, 7))
    im = ax.imshow(cross.values, cmap="PuBuGn", aspect="auto")

    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels(cross.columns, rotation=45, ha="right")
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index)

    for i in range(len(cross.index)):
        for j in range(len(cross.columns)):
            val = cross.values[i, j]
            if val > 0:
                ax.text(j, i, str(val), ha="center", va="center", fontsize=10,
                        color="white" if val > cross.values.max() * 0.5 else "black")

    ax.set_title("Publishers and their cities (publishers with 2+ books)")
    fig.colorbar(im, ax=ax, label="Number of books", shrink=0.8)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/14_publisher_place.png", bbox_inches="tight")
    plt.close(fig)
    print("  14_publisher_place.png")


# ════════════════════════════════════════════════════════════
# FIGURE 15: Author publishing timeline
# ════════════════════════════════════════════════════════════

def fig_author_timeline():
    """Timeline showing when each multi-book author published, colored by language."""
    sub = df[
        (df["author_display"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    auth_counts = sub["author_display"].value_counts()
    multi = auth_counts[auth_counts >= 2].index
    sub = sub[sub["author_display"].isin(multi)]

    # Order authors by earliest publication
    auth_order = sub.groupby("author_display")["year_normalized"].min().sort_values().index

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7",
    }

    def get_lang_color(lang):
        for key, color in lang_colors.items():
            if key in str(lang):
                return color
        return "#BAB0AC"

    fig, ax = plt.subplots(figsize=(13, 8))

    for i, author in enumerate(auth_order):
        ws = sub[sub["author_display"] == author]
        for _, row in ws.iterrows():
            c = get_lang_color(row["language_normalized"])
            ax.scatter(row["year_normalized"], i, color=c, s=80, zorder=3,
                       edgecolors="white", linewidth=0.5)
        years = ws["year_normalized"].values
        if len(years) > 1:
            ax.plot([years.min(), years.max()], [i, i],
                    color="#AAAAAA", linewidth=1, alpha=0.5, zorder=1)

    ax.set_yticks(range(len(auth_order)))
    ax.set_yticklabels(auth_order, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Publication year")
    ax.set_title("Author publication timelines (colored by language)")
    ax.grid(axis="x", alpha=0.3)

    # Legend for languages
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=l)
               for l, c in lang_colors.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/15_author_timeline.png", bbox_inches="tight")
    plt.close(fig)
    print("  15_author_timeline.png")


# ════════════════════════════════════════════════════════════
# FIGURE 16: Place × Language — which cities published in which languages?
# ════════════════════════════════════════════════════════════

def fig_place_language():
    """Stacked bar: top publication places, split by language."""
    sub = df[
        (df["place_normalized"] != "") &
        (df["language_normalized"] != "")
    ].copy()

    def simplify_lang(lang):
        if "German" in lang and "Latin" in lang:
            return "German + Latin"
        for l in ["German", "Latin", "Italian", "French", "English"]:
            if l in lang:
                return l
        return "Other"

    sub["lang_simple"] = sub["language_normalized"].apply(simplify_lang)

    top_places = sub["place_normalized"].value_counts().head(12).index
    sub = sub[sub["place_normalized"].isin(top_places)]

    cross = pd.crosstab(sub["place_normalized"], sub["lang_simple"])
    cross = cross.loc[top_places]

    lang_order = ["Latin", "German", "German + Latin", "Italian", "French", "English", "Other"]
    lang_order = [l for l in lang_order if l in cross.columns]
    cross = cross[lang_order]

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7", "Other": "#BAB0AC"
    }

    fig, ax = plt.subplots(figsize=(12, 6))
    left = np.zeros(len(cross))
    for lang in lang_order:
        vals = cross[lang].values
        ax.barh(range(len(cross)), vals, left=left,
                label=lang, color=lang_colors.get(lang, "#999"),
                edgecolor="white", linewidth=0.5)
        left += vals

    ax.set_yticks(range(len(cross)))
    ax.set_yticklabels(cross.index)
    ax.invert_yaxis()
    ax.set_xlabel("Number of books")
    ax.set_title("Publication places by language (top 12 cities)")
    ax.legend(loc="lower right", fontsize=9)
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/16_place_language.png", bbox_inches="tight")
    plt.close(fig)
    print("  16_place_language.png")


# ════════════════════════════════════════════════════════════
# FIGURE 17: Edition languages — how works shifted language
# ════════════════════════════════════════════════════════════

def fig_edition_languages():
    """For works with multiple editions, show how language changed across editions."""
    sub = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna()) &
        (df["language_normalized"] != "")
    ].copy()

    group_sizes = sub["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index
    sub = sub[sub["short_title_likely_identical_shared"].isin(multi)]

    # Only keep groups where language actually varies
    def has_lang_variation(g):
        langs = set()
        for lang in g["language_normalized"]:
            if "German" in lang and "Latin" in lang:
                langs.add("German + Latin")
            elif "German" in lang:
                langs.add("German")
            elif "Latin" in lang:
                langs.add("Latin")
            else:
                langs.add(lang)
        return len(langs) > 1

    varied = sub.groupby("short_title_likely_identical_shared").filter(has_lang_variation)

    if len(varied) == 0:
        print("  17_edition_languages.png — skipped (no language variation)")
        return

    group_order = varied.groupby("short_title_likely_identical_shared")["year_normalized"].min().sort_values().index

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7",
    }

    def get_lang_color(lang):
        for key, color in lang_colors.items():
            if key in str(lang):
                return color
        return "#BAB0AC"

    fig, ax = plt.subplots(figsize=(13, 6))

    for i, work in enumerate(group_order):
        ws = varied[varied["short_title_likely_identical_shared"] == work].sort_values("year_normalized")
        for _, row in ws.iterrows():
            c = get_lang_color(row["language_normalized"])
            ax.scatter(row["year_normalized"], i, color=c, s=100, zorder=3,
                       edgecolors="white", linewidth=0.5)
        years = ws["year_normalized"].values
        if len(years) > 1:
            ax.plot(years, [i] * len(years), color="#AAAAAA", linewidth=1.5, alpha=0.4, zorder=1)

    ax.set_yticks(range(len(group_order)))
    ax.set_yticklabels([g if len(g) <= 40 else g[:37] + "..." for g in group_order], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Publication year")
    ax.set_title("Language of editions/translations over time")
    ax.grid(axis="x", alpha=0.3)

    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=l)
               for l, c in lang_colors.items()]
    ax.legend(handles=handles, loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/17_edition_languages.png", bbox_inches="tight")
    plt.close(fig)
    print("  17_edition_languages.png")


# ════════════════════════════════════════════════════════════
# FIGURE 18: Edition detail cards — place, language, publisher per edition
# ════════════════════════════════════════════════════════════

def fig_edition_detail():
    """Detailed view of each multi-edition work: year, place, language, publisher.
    Uses a two-column layout: timeline on the left, details table on the right."""
    from matplotlib.lines import Line2D

    sub = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    group_sizes = sub["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index
    sub = sub[sub["short_title_likely_identical_shared"].isin(multi)]

    group_order = sub.groupby("short_title_likely_identical_shared")["year_normalized"].min().sort_values().index

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7",
    }

    def get_lang_color(lang):
        for key, color in lang_colors.items():
            if key in str(lang):
                return color
        return "#BAB0AC"

    # Collect rows with y positions
    plot_rows = []
    y_pos = 0
    prev_work = None
    for work in group_order:
        ws = sub[sub["short_title_likely_identical_shared"] == work].sort_values("year_normalized")
        for _, row in ws.iterrows():
            if prev_work is not None and work != prev_work:
                y_pos += 0.6
            plot_rows.append((y_pos, work, row))
            prev_work = work
            y_pos += 1

    total_rows = y_pos

    fig, (ax_timeline, ax_info) = plt.subplots(
        1, 2, figsize=(20, max(10, total_rows * 0.45)),
        gridspec_kw={"width_ratios": [3, 4], "wspace": 0.05}
    )

    y_label_positions = []
    prev_work = None

    for yp, work, row in plot_rows:
        year = row["year_normalized"]
        place = row["place_normalized"] if row["place_normalized"] != "" else "?"
        lang = row["language_normalized"]
        pub = row["publisher_normalized_inferred"] if row["publisher_normalized_inferred"] != "" else row["publisher_normalized"]
        if pub == "":
            pub = "?"

        c = get_lang_color(lang)
        ax_timeline.scatter(year, yp, color=c, s=100, zorder=3, edgecolors="white", linewidth=0.5)

        if work != prev_work:
            y_label_positions.append((yp, work if len(work) <= 42 else work[:39] + "..."))
        else:
            y_label_positions.append((yp, ""))
        prev_work = work

        # Right panel: text details
        detail = f"{int(year)}  ·  {place}  ·  {pub}  ·  {lang}"
        ax_info.text(0.02, yp, detail, va="center", fontsize=9, fontfamily="monospace",
                     color="#333333")

    ax_timeline.set_yticks([y for y, _ in y_label_positions])
    ax_timeline.set_yticklabels([l for _, l in y_label_positions], fontsize=9)
    ax_timeline.invert_yaxis()
    ax_timeline.set_xlabel("Publication year")
    ax_timeline.grid(axis="x", alpha=0.3)

    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=l)
               for l, c in lang_colors.items()]
    ax_timeline.legend(handles=handles, loc="lower left", fontsize=9)

    ax_info.set_ylim(ax_timeline.get_ylim())
    ax_info.set_xlim(0, 1)
    ax_info.axis("off")
    ax_info.set_title("Year  ·  Place  ·  Publisher  ·  Language", fontsize=10, loc="left", pad=10)

    fig.suptitle("Editions and translations: place, publisher, and language", fontsize=13, y=1.01)
    fig.subplots_adjust(wspace=0.05)
    fig.savefig(f"{OUTPUT_DIR}/18_edition_detail.png", bbox_inches="tight")
    plt.close(fig)
    print("  18_edition_detail.png")


# ════════════════════════════════════════════════════════════
# FIGURE 19: Translation flows — Sankey-like: original language → translation language
# ════════════════════════════════════════════════════════════

def fig_translation_flows():
    """Show which works were translated and between which languages."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch

    sub = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna()) &
        (df["language_normalized"] != "")
    ].copy()

    group_sizes = sub["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index

    def simplify_lang(lang):
        if "German" in lang and "Latin" in lang:
            return "German + Latin"
        for l in ["German", "Latin", "Italian", "French", "English"]:
            if l in lang:
                return l
        return "Other"

    # For each group, find the earliest edition's language and later translations
    flows = []  # (from_lang, to_lang, work_title)
    for work in multi:
        ws = sub[sub["short_title_likely_identical_shared"] == work].sort_values("year_normalized")
        langs = [simplify_lang(l) for l in ws["language_normalized"]]
        unique_langs = list(dict.fromkeys(langs))  # preserve order, deduplicate
        if len(unique_langs) >= 2:
            orig = unique_langs[0]
            for tgt in unique_langs[1:]:
                flows.append((orig, tgt, work))

    if not flows:
        print("  19_translation_flows.png — skipped (no translation flows)")
        return

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7", "Other": "#BAB0AC"
    }

    # Build a matrix-like view
    all_langs = list(dict.fromkeys([f[0] for f in flows] + [f[1] for f in flows]))

    fig, ax = plt.subplots(figsize=(12, 7))

    # Draw arrows between languages with work labels
    y_positions = {lang: i for i, lang in enumerate(all_langs)}
    arrow_groups = {}
    for orig, tgt, work in flows:
        key = (orig, tgt)
        if key not in arrow_groups:
            arrow_groups[key] = []
        arrow_groups[key].append(work)

    # Place languages as nodes on left and right
    x_left = 0.2
    x_right = 0.8

    for lang in all_langs:
        y = y_positions[lang]
        color = lang_colors.get(lang, "#BAB0AC")
        ax.scatter([x_left, x_right], [y, y], s=300, color=color, zorder=5, edgecolors="white", linewidth=1)
        ax.text(x_left - 0.05, y, lang, ha="right", va="center", fontsize=11, fontweight="bold")
        ax.text(x_right + 0.05, y, lang, ha="left", va="center", fontsize=11, fontweight="bold")

    ax.text(x_left, -0.8, "Original\nlanguage", ha="center", va="center", fontsize=10, fontstyle="italic")
    ax.text(x_right, -0.8, "Translation\nlanguage", ha="center", va="center", fontsize=10, fontstyle="italic")

    for (orig, tgt), works in arrow_groups.items():
        y_from = y_positions[orig]
        y_to = y_positions[tgt]
        color = lang_colors.get(orig, "#BAB0AC")

        ax.annotate("", xy=(x_right - 0.02, y_to), xytext=(x_left + 0.02, y_from),
                    arrowprops=dict(arrowstyle="->", color=color, lw=2, alpha=0.6,
                                    connectionstyle=f"arc3,rad={0.1 * (1 if y_to > y_from else -1)}"))

        # Label with work titles
        mid_x = (x_left + x_right) / 2
        mid_y = (y_from + y_to) / 2
        label = "\n".join(w if len(w) <= 30 else w[:27] + "..." for w in works)
        ax.text(mid_x, mid_y, label, ha="center", va="center", fontsize=8,
                bbox=dict(boxstyle="round,pad=0.3", facecolor="white", edgecolor="#CCCCCC", alpha=0.9))

    ax.set_xlim(-0.1, 1.1)
    ax.set_ylim(len(all_langs) - 0.5, -1.2)
    ax.axis("off")
    ax.set_title("Translation flows between languages", fontsize=13, pad=20)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/19_translation_flows.png", bbox_inches="tight")
    plt.close(fig)
    print("  19_translation_flows.png")


# ════════════════════════════════════════════════════════════
# FIGURE 20: Author output — all books by prolific authors with details
# ════════════════════════════════════════════════════════════

def fig_author_works_detail():
    """For authors with 3+ books, one subplot per author with each book on its own row."""
    from matplotlib.lines import Line2D

    sub = df[
        (df["author_display"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    auth_counts = sub["author_display"].value_counts()
    prolific = auth_counts[auth_counts >= 3].index
    sub = sub[sub["author_display"].isin(prolific)]

    auth_order = sub.groupby("author_display")["year_normalized"].min().sort_values().index
    n_authors = len(auth_order)

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7",
    }

    def get_lang_color(lang):
        for key, color in lang_colors.items():
            if key in str(lang):
                return color
        return "#BAB0AC"

    fig, axes = plt.subplots(n_authors, 1, figsize=(16, n_authors * 2.2),
                             sharex=True)
    if n_authors == 1:
        axes = [axes]

    for idx, author in enumerate(auth_order):
        ax = axes[idx]
        ws = sub[sub["author_display"] == author].sort_values("year_normalized")
        n_books = len(ws)

        for j, (_, row) in enumerate(ws.iterrows()):
            year = row["year_normalized"]
            c = get_lang_color(row["language_normalized"])
            place = row["place_normalized"] if row["place_normalized"] != "" else "?"
            st = str(row["short_title"])
            if len(st) > 30:
                st = st[:27] + "..."
            lang = row["language_normalized"]

            ax.scatter(year, j, color=c, s=120, zorder=3, edgecolors="white", linewidth=0.5)

            # Label to the right: title, place, language
            label = f"{st}  ({place}, {lang})"
            ax.annotate(label, (year, j), textcoords="offset points", xytext=(14, 0),
                        fontsize=8.5, va="center")

            # Year label to the left of dot
            ax.annotate(str(int(year)), (year, j), textcoords="offset points", xytext=(-10, 0),
                        fontsize=8, va="center", ha="right", color="#666666")

        ax.set_yticks([])
        ax.set_ylim(-0.7, n_books - 0.3)
        ax.invert_yaxis()
        ax.set_ylabel(author, fontsize=10, fontweight="bold", rotation=0, ha="right", va="center",
                      labelpad=10)
        ax.grid(axis="x", alpha=0.2)

        # Light background shading alternating
        if idx % 2 == 1:
            ax.set_facecolor("#F8F8F8")

    axes[-1].set_xlabel("Publication year")
    fig.suptitle("Prolific authors (3+ books): works by year, place, and language",
                 fontsize=13, y=1.005)

    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=l)
               for l, c in lang_colors.items()]
    fig.legend(handles=handles, loc="upper right", fontsize=9, title="Language",
               bbox_to_anchor=(0.99, 0.99))

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/20_author_works_detail.png", bbox_inches="tight")
    plt.close(fig)
    print("  20_author_works_detail.png")


# ════════════════════════════════════════════════════════════
# FIGURE 21: Edition longevity — how long did works stay in print?
# ════════════════════════════════════════════════════════════

def fig_edition_longevity():
    """Bar chart showing the time span between first and last edition for each work."""
    sub = df[
        (df["short_title_likely_identical_shared"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    group_sizes = sub["short_title_likely_identical_shared"].value_counts()
    multi = group_sizes[group_sizes >= 2].index
    sub = sub[sub["short_title_likely_identical_shared"].isin(multi)]

    records = []
    for work in multi:
        ws = sub[sub["short_title_likely_identical_shared"] == work]
        years = ws["year_normalized"].astype(float)
        n_editions = len(ws)
        first = int(years.min())
        last = int(years.max())
        span = last - first
        records.append({"work": work, "first": first, "last": last, "span": span, "editions": n_editions})

    recs = sorted(records, key=lambda r: -r["span"])

    fig, ax = plt.subplots(figsize=(14, 7))

    for i, rec in enumerate(recs):
        color = plt.cm.viridis(rec["span"] / max(r["span"] for r in recs) if max(r["span"] for r in recs) > 0 else 0)
        ax.barh(i, rec["span"], left=rec["first"], color=color, edgecolor="white", linewidth=0.5, height=0.7)
        # Edition count markers
        ws = sub[sub["short_title_likely_identical_shared"] == rec["work"]]
        edition_years = ws["year_normalized"].astype(float).values
        ax.scatter(edition_years, [i] * len(edition_years), color="white", s=30, zorder=4, edgecolors="black", linewidth=0.5)
        # Span label
        if rec["span"] > 0:
            ax.text(rec["last"] + 2, i, f'{rec["span"]} yrs, {rec["editions"]} ed.',
                    va="center", fontsize=8.5, color="#555555")

    ax.set_yticks(range(len(recs)))
    ax.set_yticklabels([r["work"] if len(r["work"]) <= 42 else r["work"][:39] + "..." for r in recs], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Year")
    ax.set_title("How long did works stay in print? (time span between first and last edition in dataset)")
    ax.grid(axis="x", alpha=0.3)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/21_edition_longevity.png", bbox_inches="tight")
    plt.close(fig)
    print("  21_edition_longevity.png")


# ════════════════════════════════════════════════════════════
# FIGURE 22: Author–publisher relationships
# ════════════════════════════════════════════════════════════

def fig_author_publisher():
    """Dot plot showing which authors worked with which publishers (2+ collaborations highlighted)."""
    sub = df[
        (df["author_display"] != "") &
        (df["publisher_normalized_inferred"] != "")
    ].copy()

    # Only authors with 2+ books
    auth_counts = sub["author_display"].value_counts()
    multi_auth = auth_counts[auth_counts >= 2].index
    sub = sub[sub["author_display"].isin(multi_auth)]

    # Only publishers with 2+ books in this subset
    pub_counts = sub["publisher_normalized_inferred"].value_counts()
    multi_pub = pub_counts[pub_counts >= 1].index
    sub = sub[sub["publisher_normalized_inferred"].isin(multi_pub)]

    cross = pd.crosstab(sub["author_display"], sub["publisher_normalized_inferred"])
    # Drop all-zero rows/cols
    cross = cross.loc[cross.sum(axis=1) > 0, cross.sum(axis=0) > 0]
    # Sort by total
    cross = cross.loc[cross.sum(axis=1).sort_values(ascending=False).index]
    cross = cross[cross.sum().sort_values(ascending=False).index]
    # Limit to top publishers
    cross = cross.iloc[:, :15]

    fig, ax = plt.subplots(figsize=(14, 10))

    for i in range(len(cross.index)):
        for j in range(len(cross.columns)):
            val = cross.values[i, j]
            if val > 0:
                ax.scatter(j, i, s=val * 120, color="#4878CF" if val >= 2 else "#BAB0AC",
                           edgecolors="white", linewidth=0.5, zorder=3, alpha=0.8)
                if val >= 2:
                    ax.text(j, i, str(val), ha="center", va="center", fontsize=8,
                            fontweight="bold", color="white")

    ax.set_xticks(range(len(cross.columns)))
    ax.set_xticklabels(cross.columns, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(len(cross.index)))
    ax.set_yticklabels(cross.index, fontsize=9)
    ax.set_xlim(-0.5, len(cross.columns) - 0.5)
    ax.set_ylim(len(cross.index) - 0.5, -0.5)
    ax.set_title("Author–publisher relationships (dot size = number of books)")
    ax.grid(alpha=0.15)

    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#4878CF', markersize=10, label='2+ books together'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='#BAB0AC', markersize=7, label='1 book'),
    ]
    ax.legend(handles=handles, loc="lower right", fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/22_author_publisher.png", bbox_inches="tight")
    plt.close(fig)
    print("  22_author_publisher.png")


# ════════════════════════════════════════════════════════════
# FIGURE 23: Author geographic reach — how many cities per author?
# ════════════════════════════════════════════════════════════

def fig_author_geographic_reach():
    """For authors with 2+ books, show the number of distinct publication cities."""
    sub = df[
        (df["author_display"] != "") &
        (df["place_normalized"] != "") &
        (df["year_normalized"].notna())
    ].copy()

    auth_counts = sub["author_display"].value_counts()
    multi = auth_counts[auth_counts >= 2].index
    sub = sub[sub["author_display"].isin(multi)]

    records = []
    for auth in multi:
        ws = sub[sub["author_display"] == auth]
        places = ws["place_normalized"].unique()
        n_books = len(ws)
        records.append({"author": auth, "n_cities": len(places), "n_books": n_books,
                        "cities": ", ".join(sorted(places))})

    recs = sorted(records, key=lambda r: (-r["n_cities"], -r["n_books"]))

    fig, ax = plt.subplots(figsize=(13, 8))

    colors = ["#D65F5F" if r["n_cities"] >= 3 else "#E8C170" if r["n_cities"] == 2 else "#7CAE7A"
              for r in recs]

    bars = ax.barh(range(len(recs)), [r["n_cities"] for r in recs],
                   color=colors, edgecolor="white", linewidth=0.5)
    ax.set_yticks(range(len(recs)))
    ax.set_yticklabels([r["author"] for r in recs], fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Number of distinct publication cities")
    ax.set_title("Author geographic reach (authors with 2+ books)")
    ax.xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    for i, rec in enumerate(recs):
        ax.text(rec["n_cities"] + 0.1, i, rec["cities"], va="center", fontsize=8, color="#555555")

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/23_author_geographic_reach.png", bbox_inches="tight")
    plt.close(fig)
    print("  23_author_geographic_reach.png")


# ════════════════════════════════════════════════════════════
# FIGURE 24: Publishing centers over time — when was each city active?
# ════════════════════════════════════════════════════════════

def fig_city_activity_timeline():
    """Per-city subplot timeline showing each book with title and author."""
    from matplotlib.lines import Line2D

    sub = df[
        (df["place_normalized"] != "") &
        (df["year_normalized"].notna())
    ].copy()
    sub["year_float"] = sub["year_normalized"].astype(float)

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7",
    }

    def get_lang_color(lang):
        for key, color in lang_colors.items():
            if key in str(lang):
                return color
        return "#BAB0AC"

    place_counts = sub["place_normalized"].value_counts()
    top_places = place_counts[place_counts >= 2].index
    # Sort by earliest year
    place_order = sub[sub["place_normalized"].isin(top_places)].groupby(
        "place_normalized")["year_float"].min().sort_values().index

    # Calculate total rows for figure height
    total_books = sum(len(sub[sub["place_normalized"] == p]) for p in place_order)
    n_cities = len(place_order)

    fig, axes = plt.subplots(n_cities, 1,
                             figsize=(18, max(12, total_books * 0.35 + n_cities * 0.8)),
                             sharex=True)
    if n_cities == 1:
        axes = [axes]

    for idx, place in enumerate(place_order):
        ax = axes[idx]
        ws = sub[sub["place_normalized"] == place].sort_values("year_float")
        n_books = len(ws)

        for j, (_, row) in enumerate(ws.iterrows()):
            year = row["year_float"]
            c = get_lang_color(row["language_normalized"])
            ax.scatter(year, j, color=c, s=100, zorder=3, edgecolors="white", linewidth=0.5)

            # Build label: short_title (author)
            st = str(row["short_title"])
            if len(st) > 35:
                st = st[:32] + "..."
            author = row["author_display"] if row["author_display"] != "" else "anon."
            if len(author) > 25:
                author = author[:22] + "..."
            label = f"{st}  ({author})"
            ax.annotate(label, (year, j), textcoords="offset points", xytext=(14, 0),
                        fontsize=8, va="center")

            # Year to the left
            ax.annotate(str(int(year)), (year, j), textcoords="offset points", xytext=(-10, 0),
                        fontsize=7.5, va="center", ha="right", color="#666666")

        ax.set_yticks([])
        ax.set_ylim(-0.7, n_books - 0.3)
        ax.invert_yaxis()
        ax.set_ylabel(f"{place}\n({n_books})", fontsize=10, fontweight="bold",
                      rotation=0, ha="right", va="center", labelpad=10)
        ax.grid(axis="x", alpha=0.2)

        if idx % 2 == 1:
            ax.set_facecolor("#F8F8F8")

    axes[-1].set_xlabel("Publication year")
    fig.suptitle("Publishing cities: what was published where and when",
                 fontsize=14, y=1.002)

    handles = [Line2D([0], [0], marker='o', color='w', markerfacecolor=c, markersize=8, label=l)
               for l, c in lang_colors.items()]
    fig.legend(handles=handles, loc="upper right", fontsize=9, title="Language",
               bbox_to_anchor=(0.99, 0.998))

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/24_city_activity_timeline.png", bbox_inches="tight")
    plt.close(fig)
    print("  24_city_activity_timeline.png")


# ════════════════════════════════════════════════════════════
# FIGURE 25: Language proportions over time (normalized)
# ════════════════════════════════════════════════════════════

def fig_language_proportions():
    """Normalized stacked bar: what proportion of books in each period were in each language?"""
    sub = df[
        (df["language_normalized"] != "") &
        (df["year_normalized"].notna())
    ].copy()
    sub["year_float"] = sub["year_normalized"].astype(float)

    # Use 25-year bins for smoother proportions
    bins = list(range(1500, 1776, 25))
    labels = [f"{b}–{b+24}" for b in bins[:-1]]
    sub["period"] = pd.cut(sub["year_float"], bins=bins, labels=labels, right=False)
    sub = sub.dropna(subset=["period"])

    def simplify_lang(lang):
        if "German" in lang and "Latin" in lang:
            return "German + Latin"
        for l in ["German", "Latin", "Italian", "French", "English"]:
            if l in lang:
                return l
        return "Other"

    sub["lang_simple"] = sub["language_normalized"].apply(simplify_lang)

    cross = pd.crosstab(sub["period"], sub["lang_simple"])
    lang_order = ["Latin", "German", "German + Latin", "Italian", "French", "English", "Other"]
    lang_order = [l for l in lang_order if l in cross.columns]
    cross = cross[lang_order]

    # Normalize to proportions
    cross_pct = cross.div(cross.sum(axis=1), axis=0) * 100

    lang_colors = {
        "Latin": "#4878CF", "German": "#D65F5F", "German + Latin": "#B07AA1",
        "Italian": "#59A14F", "French": "#EDC948", "English": "#FF9DA7", "Other": "#BAB0AC"
    }

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9), gridspec_kw={"height_ratios": [3, 1]})

    # Top: proportional stacked bars
    bottom = np.zeros(len(cross_pct))
    for lang in lang_order:
        vals = cross_pct[lang].values
        ax1.bar(range(len(cross_pct)), vals, bottom=bottom,
                label=lang, color=lang_colors.get(lang, "#999"),
                edgecolor="white", linewidth=0.3, width=0.85)
        bottom += vals

    ax1.set_xticks(range(len(cross_pct)))
    ax1.set_xticklabels(cross_pct.index, rotation=45, ha="right", fontsize=9)
    ax1.set_ylabel("Percentage")
    ax1.set_title("Language proportions by quarter-century")
    ax1.legend(loc="upper right", fontsize=9)
    ax1.set_ylim(0, 100)

    # Bottom: total book count per period
    totals = cross.sum(axis=1)
    ax2.bar(range(len(totals)), totals.values, color="#AAAAAA", edgecolor="white", width=0.85)
    ax2.set_xticks(range(len(totals)))
    ax2.set_xticklabels(totals.index, rotation=45, ha="right", fontsize=9)
    ax2.set_ylabel("Total books")
    ax2.set_title("Sample size per period", fontsize=10)
    ax2.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/25_language_proportions.png", bbox_inches="tight")
    plt.close(fig)
    print("  25_language_proportions.png")


# ════════════════════════════════════════════════════════════
# Run all
# ════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"Generating figures in {OUTPUT_DIR}/\n")
    fig_books_per_decade()
    fig_publication_places()
    fig_languages()
    fig_top_authors()
    fig_pages_per_book()
    fig_edition_groups()
    fig_timeline_scatter()
    fig_collection_overview()
    fig_place_decade_heatmap()
    fig_author_place_network()
    fig_publisher_decade()
    fig_language_over_time()
    fig_edition_spread()
    fig_publisher_place()
    fig_author_timeline()
    fig_place_language()
    fig_edition_languages()
    fig_edition_detail()
    fig_translation_flows()
    fig_author_works_detail()
    fig_edition_longevity()
    fig_author_publisher()
    fig_author_geographic_reach()
    fig_city_activity_timeline()
    fig_language_proportions()
    print(f"\nDone! {len(os.listdir(OUTPUT_DIR))} figures saved.")
