import os
import json
import logging
from datetime import datetime, timezone, date
from typing import Dict, Any

from src.storage import FileStorage

logger = logging.getLogger("DataExporter")


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder to handle datetime and date objects if any remain."""

    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)


def get_item_date(item: Dict[str, Any]) -> datetime:
    """Helper to extract and normalize date to datetime for sorting."""
    dt = item.get("date")
    if dt is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if isinstance(dt, datetime):
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    if isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time(), tzinfo=timezone.utc)
    if isinstance(dt, str):
        try:
            # Try parsing ISO format
            parsed = datetime.fromisoformat(dt.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return datetime.min.replace(tzinfo=timezone.utc)


def export_data(
    base_raw_dir: str = "data/raw",
    output_dir: str = "data/processed",
    max_size_mb: float = 5.0,
) -> str:
    """Loads raw Parquet data, integrates it, applies file size constraints,

    and exports a unified JSON file for static Web UI usage.
    """
    logger.info("Starting data integration and export process...")
    storage = FileStorage(base_dir=base_raw_dir)

    # 1. Load all raw data
    cves = storage.load_cves()
    epss_list = storage.load_epss()
    kev_list = storage.load_kev()
    cwes = storage.load_cwe()
    arxiv = storage.load_arxiv()
    repos = storage.load_github()
    ghsas = storage.load_ghsa()
    articles = storage.load_articles()
    news = storage.load_news()
    nist = storage.load_nist()
    atlas_tactics = storage.load_atlas_tactics()
    atlas_techniques = storage.load_atlas_techniques()
    atlas_case_studies = storage.load_atlas_case_studies()
    keywords = storage.load_notion_keywords()
    products = storage.load_notion_products()

    # 2. Build lookup maps for faster integration
    epss_map = {e.cve_id: e.model_dump(mode="json") for e in epss_list}
    kev_map = {k.cve_id: k.model_dump(mode="json") for k in kev_list}
    cwe_map = {c.cwe_id: c.model_dump(mode="json") for c in cwes}

    # Track which GHSAs are mapped to CVEs to avoid duplication in separate advisories list
    cve_to_ghsa_map = {}
    for g in ghsas:
        if g.cve_id:
            if g.cve_id not in cve_to_ghsa_map:
                cve_to_ghsa_map[g.cve_id] = []
            cve_to_ghsa_map[g.cve_id].append(g.model_dump(mode="json"))

    # 3. Integrate CVE details
    extended_cves = []
    for cve in cves:
        cve_dict = cve.model_dump(mode="json")
        cve_id = cve.cve_id

        # Attach EPSS score
        cve_dict["epss"] = epss_map.get(cve_id)

        # Attach CISA KEV information
        kev_info = kev_map.get(cve_id)
        cve_dict["is_kev"] = kev_info is not None
        cve_dict["kev_info"] = kev_info

        # Attach CWE details
        cve_dict["cwes"] = [
            cwe_map[cwe_id] for cwe_id in cve.cwe_ids if cwe_id in cwe_map
        ]

        # Attach GHSA advisories
        cve_dict["advisories"] = cve_to_ghsa_map.get(cve_id, [])

        extended_cves.append(cve_dict)

    # Separate GHSAs that have no associated CVE ID
    standalone_ghsas = [g.model_dump(mode="json") for g in ghsas if not g.cve_id]

    # 4. Prepare JSON Structure (Metadata & Master data first)
    export_dict = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "keywords": [k.model_dump(mode="json") for k in keywords],
            "products": [p.model_dump(mode="json") for p in products],
            "totals": {
                "cves": len(cves),
                "arxiv": len(arxiv),
                "rss_articles": len(articles),
                "rss_news": len(news),
                "github_repos": len(repos),
            },
        },
        "nist_controls": [n.model_dump(mode="json") for n in nist],
        "atlas": {
            "tactics": [t.model_dump(mode="json") for t in atlas_tactics],
            "techniques": [te.model_dump(mode="json") for te in atlas_techniques],
            "case_studies": [c.model_dump(mode="json") for c in atlas_case_studies],
        },
        "github_repos": [r.model_dump(mode="json") for r in repos],
        "cves": [],
        "arxiv": [],
        "rss_articles": [],
        "rss_news": [],
        "ghsa_advisories": [],
    }

    # Calculate initial size (base skeleton size)
    base_json_str = json.dumps(export_dict, cls=DateTimeEncoder, ensure_ascii=False)
    current_size = len(base_json_str.encode("utf-8"))

    max_bytes = int(max_size_mb * 1024 * 1024)
    # Target 90% of max size to leave a safety margin
    target_max_bytes = int(max_bytes * 0.9)

    logger.info(
        f"Base JSON skeleton size: {current_size} bytes. Target limit: {target_max_bytes} bytes ({max_size_mb} MB limit)"
    )

    # 5. Compile time-series items to sort and dynamically add
    time_series_items = []

    # Add CVEs
    for cve in extended_cves:
        time_series_items.append(
            {"date": cve.get("published_at"), "category": "cves", "data": cve}
        )

    # Add ArXiv Papers
    for paper in arxiv:
        paper_dict = paper.model_dump(mode="json")
        time_series_items.append(
            {
                "date": paper_dict.get("published_at"),
                "category": "arxiv",
                "data": paper_dict,
            }
        )

    # Add RSS Articles
    for article in articles:
        art_dict = article.model_dump(mode="json")
        time_series_items.append(
            {
                "date": art_dict.get("published_at"),
                "category": "rss_articles",
                "data": art_dict,
            }
        )

    # Add RSS News
    for n in news:
        news_dict = n.model_dump(mode="json")
        time_series_items.append(
            {
                "date": news_dict.get("published_at"),
                "category": "rss_news",
                "data": news_dict,
            }
        )

    # Add Standalone GHSAs
    for g in standalone_ghsas:
        time_series_items.append(
            {"date": g.get("published_at"), "category": "ghsa_advisories", "data": g}
        )

    # Sort all items by date DESC (newest first)
    time_series_items.sort(key=get_item_date, reverse=True)
    logger.info(f"Total time-series items to evaluate: {len(time_series_items)}")

    # 6. Dynamically add items while tracking simulated JSON size
    added_counts = {
        "cves": 0,
        "arxiv": 0,
        "rss_articles": 0,
        "rss_news": 0,
        "ghsa_advisories": 0,
    }

    dropped_count = 0

    # We estimate size growth instead of calling json.dumps() on the entire dict in each loop
    # comma and brackets: each item in list roughly adds length of JSON + 2 bytes (comma & formatting)
    for item in time_series_items:
        category = item["category"]
        item_data = item["data"]

        # Serialize only this item to measure its size contribution
        item_json = json.dumps(item_data, cls=DateTimeEncoder, ensure_ascii=False)
        item_size = (
            len(item_json.encode("utf-8")) + 2
        )  # extra bytes for list structure formatting

        if current_size + item_size > target_max_bytes:
            # We reached the size limit cutoff
            dropped_count += 1
            continue

        # Add item to its respective list in export_dict
        export_dict[category].append(item_data)
        current_size += item_size
        added_counts[category] += 1

    logger.info(f"JSON assembly completed. Final estimated size: {current_size} bytes.")
    logger.info(f"Added items: {added_counts}")
    if dropped_count > 0:
        logger.warning(
            f"File size limit reached! Omitted {dropped_count} older items from JSON export."
        )

    # 7. Write to file
    os.makedirs(output_dir, exist_ok=True)
    output_filepath = os.path.join(output_dir, "dashboard_data.json")

    with open(output_filepath, "w", encoding="utf-8") as f:
        json.dump(export_dict, f, cls=DateTimeEncoder, ensure_ascii=False, indent=2)

    actual_size = os.path.getsize(output_filepath)
    logger.info(
        f"Successfully exported data mart to {output_filepath} (Actual size: {actual_size / (1024 * 1024):.2f} MB)"
    )

    return output_filepath
