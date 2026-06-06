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


def test_cisa_kev():
    print("\n========================================")
    print("Testing CISA KEV Fetcher")
    print("========================================")
    try:
        fetcher = CISAKEVFetcher()
        # Fetch data (CISA KEV is large, we can inspect first few)
        results = fetcher.fetch()
        print(f"Total parsed KEV models: {len(results)}")
        if results:
            print("\nFirst 3 parsed records:")
            for idx, item in enumerate(results[:3]):
                print(
                    f"[{idx + 1}] CVE: {item.cve_id} | Product: {item.product} | Name: {item.vulnerablity_name} | Added: {item.added_date}"
                )
    except Exception as e:
        print(f"Error testing KISA KEV: {e}", file=sys.stderr)


def test_first_epss():
    print("\n========================================")
    print("Testing FIRST EPSS Fetcher")
    print("========================================")
    try:
        fetcher = FIRSTEPSSFetcher()
        # We query for specific well-known CVEs
        cve_ids = ["CVE-2021-44228", "CVE-2023-38606"]
        results = fetcher.fetch(cve_ids=cve_ids)
        print(f"Total parsed EPSS models: {len(results)}")
        for idx, item in enumerate(results):
            print(
                f"[{idx + 1}] CVE: {item.cve_id} | EPSS: {item.epss} | Percentile: {item.percentile} | Date: {item.date}"
            )
    except Exception as e:
        print(f"Error testing FIRST EPSS: {e}", file=sys.stderr)


def test_nvd_cve():
    print("\n========================================")
    print("Testing NVD CVE Fetcher")
    print("========================================")
    try:
        fetcher = NVDCVEFetcher()
        # Search AI related CVEs, limit to 3
        results = fetcher.fetch(keyword="prompt injection", limit=3)
        print(f"Total parsed CVE models: {len(results)}")
        for idx, item in enumerate(results):
            print(
                f"[{idx + 1}] CVE: {item.cve_id} | Published: {item.published_at} | CVSS: {item.cvss_base_score} ({item.cvss_base_label})"
            )
            print(f"    Description: {item.description[:150]}...")
            print(f"    CWEs: {item.cwe_ids}")

        # Test 2: Fetch latest CVEs (no keyword, using default 14-days pub date filter)
        print("\nTesting NVD CVE Fetcher - Latest CVEs (Last 14 days)")
        latest_results = fetcher.fetch(limit=3)
        print(f"Total parsed latest CVE models: {len(latest_results)}")
        for idx, item in enumerate(latest_results):
            print(
                f"[{idx + 1}] CVE: {item.cve_id} | Published: {item.published_at} | CVSS: {item.cvss_base_score} ({item.cvss_base_label})"
            )
    except Exception as e:
        print(f"Error testing NVD CVE: {e}", file=sys.stderr)


def test_arxiv():
    print("\n========================================")
    print("Testing arXiv Fetcher")
    print("========================================")
    try:
        fetcher = ArXivFetcher()
        # Fetch top 3 papers on prompt injection
        results = fetcher.fetch(query='all:"prompt injection"', limit=3)
        print(f"Total parsed ArXiv models: {len(results)}")
        for idx, item in enumerate(results):
            print(f"[{idx + 1}] ID: {item.arxiv_id} | Published: {item.published_at}")
            print(f"    Title: {item.title}")
            print(f"    Authors: {', '.join(item.authors)}")
            print(f"    PDF URL: {item.pdf_url}")
    except Exception as e:
        print(f"Error testing arXiv: {e}", file=sys.stderr)


def test_github():
    print("\n========================================")
    print("Testing GitHub Repo Fetcher")
    print("========================================")
    try:
        fetcher = GitHubRepoFetcher()
        # Fetch LangChain repo info
        results = fetcher.fetch(repo_names=["langchain-ai/langchain"])
        print(f"Total parsed GitHubRepo models: {len(results)}")
        for idx, item in enumerate(results):
            print(
                f"[{idx + 1}] ID: {item.repo_id} | Full Name: {item.full_name} | Stars: {item.stars}"
            )
            print(f"    URL: {item.html_url}")
            print(f"    Topics: {item.topics}")
    except Exception as e:
        print(f"Error testing GitHub: {e}", file=sys.stderr)


def test_notion():
    print("\n========================================")
    print("Testing Notion Fetcher (Requires API Setup)")
    print("========================================")
    try:
        fetcher = NotionFetcher()
        # Since this requires configured API credentials, it will raise ValueError if not set
        print("Notion configuration valid. Querying databases...")
        sources = fetcher.fetch_sources()
        print(f"Total parsed sources: {len(sources)}")
        for idx, item in enumerate(sources[:3]):
            print(
                f"Source [{idx + 1}]: {item.name} | Type: {item.type} | URL: {item.url}"
            )

        keywords = fetcher.fetch_keywords()
        print(f"Total parsed keywords: {len(keywords)}")
        for idx, item in enumerate(keywords[:3]):
            print(
                f"Keyword [{idx + 1}]: {item.keyword} | Category: {item.category} | Weight: {item.weight}"
            )

        products = fetcher.fetch_products()
        print(f"Total parsed products: {len(products)}")
        for idx, item in enumerate(products[:3]):
            print(
                f"Product [{idx + 1}]: {item.product_name} | Vendor: {item.vendor} | Aliases: {item.aliases}"
            )

    except ValueError as ve:
        # Expected error if credentials are not configured in environment
        print(
            f"Notion Configuration Error (as expected if credentials are not set): {ve}"
        )
    except Exception as e:
        print(f"Error querying Notion API: {e}", file=sys.stderr)


def main():
    print("Starting Security-for-AI-Monitor Data Acquisition Test Suite")

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
