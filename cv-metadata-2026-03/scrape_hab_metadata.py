#!/usr/bin/env python3
"""
Scrape metadata from HAB digital library TEI XML for all signatures
in the HAB dataset. Saves scraped fields as new columns alongside originals.
"""

import pandas as pd
import xml.etree.ElementTree as ET
import urllib.request
import time
import sys

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

def fetch_tei_xml(signature):
    """Fetch tei-struct.xml for a given HAB signature."""
    url = f"http://diglib.hab.de/drucke/{signature}/tei-struct.xml"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (metadata research)"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            # Check if it's actually XML (not a 404 HTML page)
            if b"<TEI" in content or b"<tei" in content:
                return content
            return None
    except Exception as e:
        print(f"  ERROR fetching {signature}: {e}", file=sys.stderr)
        return None


def parse_tei_metadata(xml_bytes):
    """Extract metadata from TEI XML sourceDesc/biblFull."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        return {"parse_error": str(e)}

    result = {}

    # Find sourceDesc/biblFull/titleStmt and publicationStmt
    # Try with namespace
    bibl_full = root.find(".//tei:sourceDesc/tei:biblFull", TEI_NS)
    if bibl_full is None:
        # Try without namespace
        bibl_full = root.find(".//{http://www.tei-c.org/ns/1.0}sourceDesc/{http://www.tei-c.org/ns/1.0}biblFull")
    if bibl_full is None:
        return {"parse_error": "no biblFull found"}

    # Title
    title_el = bibl_full.find(".//tei:titleStmt/tei:title", TEI_NS)
    if title_el is not None and title_el.text:
        result["scraped_title"] = title_el.text.strip()

    # Author(s)
    authors = bibl_full.findall(".//tei:titleStmt/tei:author", TEI_NS)
    if authors:
        author_list = []
        for a in authors:
            if a.text and a.text.strip():
                author_list.append(a.text.strip())
        result["scraped_author"] = "; ".join(author_list)

    # Publication info
    pub_stmt = bibl_full.find(".//tei:publicationStmt", TEI_NS)
    if pub_stmt is not None:
        # PPN
        idno = pub_stmt.find("tei:idno[@type='PPN']", TEI_NS)
        if idno is not None and idno.text:
            result["scraped_ppn"] = idno.text.strip()

        # Publisher(s)
        publishers = pub_stmt.findall("tei:publisher", TEI_NS)
        if publishers:
            pub_list = [p.text.strip() for p in publishers if p.text and p.text.strip()]
            result["scraped_publisher"] = "; ".join(pub_list)

        # Place(s)
        places = pub_stmt.findall("tei:pubPlace", TEI_NS)
        if places:
            place_list = [p.text.strip() for p in places if p.text and p.text.strip()]
            result["scraped_place"] = "; ".join(place_list)

        # Date
        date_el = pub_stmt.find("tei:date", TEI_NS)
        if date_el is not None and date_el.text:
            result["scraped_year"] = date_el.text.strip()

    # Also grab the top-level titleStmt author/title as fallback
    top_title = root.find(".//tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:title", TEI_NS)
    top_author = root.find(".//tei:teiHeader/tei:fileDesc/tei:titleStmt/tei:author", TEI_NS)
    if "scraped_title" not in result and top_title is not None and top_title.text:
        result["scraped_title"] = top_title.text.strip()
    if "scraped_author" not in result and top_author is not None and top_author.text:
        result["scraped_author"] = top_author.text.strip()

    return result


def main():
    hab = pd.read_csv("/Users/slang/Downloads/2024-09-25_hab-dataset-img-metadata.csv",
                       keep_default_na=False)

    scraped_cols = ["scraped_title", "scraped_author", "scraped_publisher",
                    "scraped_place", "scraped_year", "scraped_ppn", "scrape_status"]

    for col in scraped_cols:
        hab[col] = ""

    total = len(hab)
    for idx, row in hab.iterrows():
        sig = row["signature"]
        print(f"[{idx+1}/{total}] {sig}...", end=" ", flush=True)

        xml = fetch_tei_xml(sig)
        if xml is None:
            hab.at[idx, "scrape_status"] = "no_tei_xml"
            print("no TEI XML")
            continue

        meta = parse_tei_metadata(xml)
        if "parse_error" in meta:
            hab.at[idx, "scrape_status"] = f"parse_error: {meta['parse_error']}"
            print(f"parse error: {meta['parse_error']}")
            continue

        for key, val in meta.items():
            if key in scraped_cols:
                hab.at[idx, key] = val

        hab.at[idx, "scrape_status"] = "ok"
        fields_found = [k for k in meta if k != "parse_error"]
        print(f"ok ({', '.join(fields_found)})")

        # Be polite to the server
        time.sleep(0.3)

    # Save with all original + scraped columns
    output_path = "/Users/slang/claude/hab_scraped_metadata.csv"
    hab.to_csv(output_path, index=False, encoding="utf-8-sig")

    print(f"\n{'='*60}")
    print(f"Output: {output_path}")
    print(f"Total: {total}")
    ok = (hab["scrape_status"] == "ok").sum()
    print(f"Successfully scraped: {ok}")
    print(f"No TEI XML: {(hab['scrape_status'] == 'no_tei_xml').sum()}")
    print(f"Parse errors: {total - ok - (hab['scrape_status'] == 'no_tei_xml').sum()}")

    print(f"\nScraped field coverage:")
    for col in scraped_cols[:-1]:
        filled = (hab[col].astype(str).str.strip() != "").sum()
        print(f"  {col}: {filled}/{total}")


if __name__ == "__main__":
    main()
