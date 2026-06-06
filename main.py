import os
import sys
import time
from dotenv import load_dotenv

# Ensure the root directory and src directory are in the python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.cisa_kev import CISAKEVFetcher  # noqa: E402
from src.first_epss import FIRSTEPSSFetcher  # noqa: E402
from src.nvd_cve import NVDCVEFetcher  # noqa: E402
from src.arxiv import ArXivFetcher  # noqa: E402
from src.github_repo import GitHubRepoFetcher  # noqa: E402
from src.notion_source import NotionFetcher  # noqa: E402
from src.storage import FileStorage  # noqa: E402

# Initialize FileStorage (uses default root data/raw)
storage = FileStorage()


def test_cisa_kev():
    print("\n========================================")
    print("Testing CISA KEV Fetcher & Storage")
    print("========================================")
    try:
        fetcher = CISAKEVFetcher()
        # Fetch data
        results = fetcher.fetch()
        print(f"Total parsed KEV models: {len(results)}")

        # Save to Parquet
        storage.save_kev(results)
        print("CISA KEV models successfully saved to Parquet.")

        # Load from Parquet
        loaded = storage.load_kev()
        print(f"Total loaded KEV models from Parquet: {len(loaded)}")

        if loaded:
            print("\nFirst 3 loaded records from Parquet:")
            for idx, item in enumerate(loaded[:3]):
                print(
                    f"[{idx + 1}] CVE: {item.cve_id} | Product: {item.product} | Name: {item.vulnerablity_name} | Added: {item.added_date}"
                )
    except Exception as e:
        print(f"Error testing CISA KEV: {e}", file=sys.stderr)


def test_first_epss():
    print("\n========================================")
    print("Testing FIRST EPSS Fetcher & Storage")
    print("========================================")
    try:
        fetcher = FIRSTEPSSFetcher()
        # We query for specific well-known CVEs
        cve_ids = ["CVE-2021-44228", "CVE-2023-38606"]
        results = fetcher.fetch(cve_ids=cve_ids)
        print(f"Total parsed EPSS models: {len(results)}")

        # Save to Parquet
        storage.save_epss(results)
        print("EPSS models successfully saved to Parquet.")

        # Load from Parquet
        loaded = storage.load_epss()
        print(f"Total loaded EPSS models from Parquet: {len(loaded)}")

        for idx, item in enumerate(loaded):
            print(
                f"[{idx + 1}] CVE: {item.cve_id} | EPSS: {item.epss} | Percentile: {item.percentile} | Date: {item.date}"
            )
    except Exception as e:
        print(f"Error testing FIRST EPSS: {e}", file=sys.stderr)


def test_nvd_cve():
    print("\n========================================")
    print("Testing NVD CVE Fetcher & Storage")
    print("========================================")
    try:
        fetcher = NVDCVEFetcher()
        # Search AI related CVEs, limit to 3
        results = fetcher.fetch(keyword="prompt injection", limit=3)
        print(f"Total parsed CVE models matching 'prompt injection': {len(results)}")

        # Save to Parquet (Upsert will be tested when saving multiple times)
        storage.save_cves(results)
        print("CVE models saved to Parquet.")

        # Load and verify
        loaded = storage.load_cves()
        print(
            f"Total loaded CVE models from Parquet (matching/accumulated): {len(loaded)}"
        )

        for idx, item in enumerate(loaded[:3]):
            print(
                f"[{idx + 1}] CVE: {item.cve_id} | Published: {item.published_at} | CVSS: {item.cvss_base_score} ({item.cvss_base_label})"
            )
            print(f"    Description: {item.description[:150]}...")
            print(f"    CWEs: {item.cwe_ids}")
            print(f"    CPEs: {item.cpe_names[:3]} (truncated)")

        # Test 2: Fetch latest CVEs and save them to test Upsert/Accumulation
        print("\nTesting NVD CVE Fetcher - Latest CVEs (Last 14 days)")
        latest_results = fetcher.fetch(limit=3)
        print(f"Total parsed latest CVE models: {len(latest_results)}")
        storage.save_cves(latest_results)
        print("Latest CVE models saved to Parquet.")

        # Reload to see accumulated/upserted result
        loaded_all = storage.load_cves()
        print(
            f"Total accumulated CVE models in Parquet after Upsert: {len(loaded_all)}"
        )
    except Exception as e:
        print(f"Error testing NVD CVE: {e}", file=sys.stderr)


def test_arxiv():
    print("\n========================================")
    print("Testing arXiv Fetcher & Storage")
    print("========================================")
    try:
        fetcher = ArXivFetcher()
        # Fetch top 3 papers on prompt injection
        results = fetcher.fetch(query='all:"prompt injection"', limit=3)
        print(f"Total parsed ArXiv models: {len(results)}")

        # Save to Parquet
        storage.save_arxiv(results)
        print("arXiv models successfully saved to Parquet.")

        # Load from Parquet
        loaded = storage.load_arxiv()
        print(f"Total loaded ArXiv models from Parquet: {len(loaded)}")

        for idx, item in enumerate(loaded[:3]):
            print(f"[{idx + 1}] ID: {item.arxiv_id} | Published: {item.published_at}")
            print(f"    Title: {item.title}")
            print(f"    Authors: {item.authors}")
            print(f"    PDF URL: {item.pdf_url}")
    except Exception as e:
        print(f"Error testing arXiv: {e}", file=sys.stderr)


def test_github():
    print("\n========================================")
    print("Testing GitHub Repo Fetcher & Storage")
    print("========================================")
    try:
        fetcher = GitHubRepoFetcher()
        # Fetch LangChain repo info
        results = fetcher.fetch(repo_names=["langchain-ai/langchain"])
        print(f"Total parsed GitHubRepo models: {len(results)}")

        # Save to Parquet
        storage.save_github(results)
        print("GitHubRepo models successfully saved to Parquet.")

        # Load from Parquet
        loaded = storage.load_github()
        print(f"Total loaded GitHubRepo models from Parquet: {len(loaded)}")

        for idx, item in enumerate(loaded):
            print(
                f"[{idx + 1}] ID: {item.repo_id} | Full Name: {item.full_name} | Stars: {item.stars}"
            )
            print(f"    URL: {item.html_url}")
            print(f"    Topics: {item.topics}")
    except Exception as e:
        print(f"Error testing GitHub: {e}", file=sys.stderr)


def test_notion():
    print("\n========================================")
    print("Testing Notion Fetcher & Storage (Requires API Setup)")
    print("========================================")
    try:
        fetcher = NotionFetcher()
        print("Notion configuration valid. Querying databases...")

        # Sources
        sources = fetcher.fetch_sources()
        print(f"Total parsed sources: {len(sources)}")
        if sources:
            storage.save_notion_sources(sources)
            print("Notion sources saved to Parquet.")
            loaded_sources = storage.load_notion_sources()
            print(f"Total loaded sources from Parquet: {len(loaded_sources)}")
            for idx, item in enumerate(loaded_sources[:3]):
                print(
                    f"  [{idx + 1}] Source: {item.name} | Type: {item.type} | URL: {item.url}"
                )

        # Keywords
        keywords = fetcher.fetch_keywords()
        print(f"Total parsed keywords: {len(keywords)}")
        if keywords:
            storage.save_notion_keywords(keywords)
            print("Notion keywords saved to Parquet.")
            loaded_keywords = storage.load_notion_keywords()
            print(f"Total loaded keywords from Parquet: {len(loaded_keywords)}")
            for idx, item in enumerate(loaded_keywords[:3]):
                print(
                    f"  [{idx + 1}] Keyword: {item.keyword} | Category: {item.category} | Weight: {item.weight}"
                )

        # Products
        products = fetcher.fetch_products()
        print(f"Total parsed products: {len(products)}")
        if products:
            storage.save_notion_products(products)
            print("Notion products saved to Parquet.")
            loaded_products = storage.load_notion_products()
            print(f"Total loaded products from Parquet: {len(loaded_products)}")
            for idx, item in enumerate(loaded_products[:3]):
                print(
                    f"  [{idx + 1}] Product: {item.product_name} | Vendor: {item.vendor} | Aliases: {item.aliases}"
                )

    except ValueError as ve:
        print(
            f"Notion Configuration Error (as expected if credentials are not set): {ve}"
        )
    except Exception as e:
        print(f"Error querying Notion API: {e}", file=sys.stderr)


def main():
    print("Starting Security-for-AI-Monitor Data Acquisition & Storage Test Suite")

    test_cisa_kev()
    time.sleep(3)
    test_first_epss()
    time.sleep(3)
    test_nvd_cve()
    time.sleep(3)
    test_arxiv()
    time.sleep(3)
    test_github()
    time.sleep(3)
    test_notion()

    print("\nTest Suite Completed.")


if __name__ == "__main__":
    main()
