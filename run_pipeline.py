import os
import sys
import time
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv

# Ensure root and src directories are in the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

from src.config import Config
from src.storage import FileStorage
from src.cisa_kev import CISAKEVFetcher
from src.first_epss import FIRSTEPSSFetcher
from src.nvd_cve import NVDCVEFetcher
from src.arxiv import ArXivFetcher
from src.github_repo import GitHubRepoFetcher
from src.notion_source import NotionFetcher
from src.mitre_atlas import ATLASFetcher
from src.cwe import CWEFetcher
from src.github_advisory import GitHubAdvisoryFetcher
from src.rss_source import RSSFetcher
from src.models import NotionSourceModel, AIKeywordModel, AIProductModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DataPipeline")


def get_default_mock_data():
    """Generates default fallback data if Notion is not configured or fails."""
    logger.warning("Using default fallback configurations for Keywords, Products, and Sources.")
    
    # 1. Default Keywords
    default_keywords = [
        AIKeywordModel(
            keyword="prompt injection",
            category="LLM Vulnerability",
            weight=1.0,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        AIKeywordModel(
            keyword="jailbreak",
            category="LLM Vulnerability",
            weight=1.0,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        AIKeywordModel(
            keyword="adversarial attack",
            category="Adversarial ML",
            weight=0.8,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        AIKeywordModel(
            keyword="model poisoning",
            category="Data Poisoning",
            weight=0.9,
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]

    # 2. Default Products
    default_products = [
        AIProductModel(
            product_name="langchain",
            vendor="langchain-ai",
            category="LLM Framework",
            aliases=["langchain-core", "langchain-community"],
            weight=1.0,
            status="active"
        ),
        AIProductModel(
            product_name="llama-index",
            vendor="run-llama",
            category="LLM Framework",
            aliases=["llamaindex"],
            weight=1.0,
            status="active"
        ),
        AIProductModel(
            product_name="ollama",
            vendor="ollama",
            category="Model Runtime",
            aliases=[],
            weight=1.0,
            status="active"
        )
    ]

    # 3. Default Sources (RSS)
    default_sources = [
        NotionSourceModel(
            source_id="mock_rss_ms_security",
            name="Microsoft Security Blog",
            url="https://www.microsoft.com/en-us/security/blog/feed/",
            type="rss",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        ),
        NotionSourceModel(
            source_id="mock_rss_openai",
            name="OpenAI Blog",
            url="https://openai.com/blog/rss.xml",
            type="rss",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
    ]

    return default_sources, default_keywords, default_products


def run_pipeline():
    logger.info("Starting Security-for-AI-Monitor Data Acquisition Pipeline")
    storage = FileStorage()
    
    # Track stats for summary
    stats = {
        "notion_sources": 0,
        "notion_keywords": 0,
        "notion_products": 0,
        "cisa_kev": 0,
        "mitre_atlas_tactics": 0,
        "mitre_atlas_techniques": 0,
        "mitre_atlas_case_studies": 0,
        "nvd_cves": 0,
        "cpes": 0,
        "arxiv_papers": 0,
        "github_repos": 0,
        "ghsa_advisories": 0,
        "epss_scores": 0,
        "cwes": 0,
        "rss_articles": 0,
        "rss_news": 0
    }

    # 1. Notion Data Loading (with Fallback)
    sources, keywords, products = [], [], []
    notion_success = False
    
    try:
        # Check Notion configuration
        Config.validate_notion_config()
        logger.info("Notion configuration validated. Fetching settings from Notion databases...")
        
        notion_fetcher = NotionFetcher()
        sources = notion_fetcher.fetch_sources()
        keywords = notion_fetcher.fetch_keywords()
        products = notion_fetcher.fetch_products()
        
        # Save Notion configuration models to storage
        if sources:
            storage.save_notion_sources(sources)
            stats["notion_sources"] = len(sources)
        if keywords:
            storage.save_notion_keywords(keywords)
            stats["notion_keywords"] = len(keywords)
        if products:
            storage.save_notion_products(products)
            stats["notion_products"] = len(products)
            
        logger.info(f"Successfully loaded configuration from Notion: {len(sources)} sources, {len(keywords)} keywords, {len(products)} products.")
        notion_success = True
    except Exception as e:
        logger.error(f"Failed to fetch data from Notion: {e}")
        sources, keywords, products = get_default_mock_data()
        stats["notion_sources"] = len(sources)
        stats["notion_keywords"] = len(keywords)
        stats["notion_products"] = len(products)

    # Filter active entries
    active_keywords = [k.keyword for k in keywords if k.status.lower() == "active"]
    active_products = [p for p in products if p.status.lower() == "active"]
    
    logger.info(f"Active Keywords to monitor: {active_keywords}")
    logger.info(f"Active Products to monitor: {[p.product_name for p in active_products]}")

    # Set of CVE IDs to dynamically query EPSS and CWE details later
    collected_cve_ids = set()

    # 2. CISA KEV (Bulk Ingestion)
    logger.info("--- [CISA KEV Ingestion] ---")
    try:
        kev_fetcher = CISAKEVFetcher()
        kev_results = kev_fetcher.fetch()
        if kev_results:
            storage.save_kev(kev_results)
            stats["cisa_kev"] = len(kev_results)
            # Add fetched CVEs to the list
            for item in kev_results:
                if item.cve_id:
                    collected_cve_ids.add(item.cve_id)
            logger.info(f"Fetched and stored {len(kev_results)} KEV vulnerability items.")
    except Exception as e:
        logger.error(f"Error fetching CISA KEV: {e}")

    # 3. MITRE ATLAS (Bulk Ingestion)
    logger.info("--- [MITRE ATLAS Ingestion] ---")
    try:
        atlas_fetcher = ATLASFetcher()
        tactics, techniques, case_studies = atlas_fetcher.fetch()
        
        storage.save_atlas_tactics(tactics)
        storage.save_atlas_techniques(techniques)
        storage.save_atlas_case_studies(case_studies)
        
        stats["mitre_atlas_tactics"] = len(tactics)
        stats["mitre_atlas_techniques"] = len(techniques)
        stats["mitre_atlas_case_studies"] = len(case_studies)
        
        logger.info(f"Fetched MITRE ATLAS data: {len(tactics)} Tactics, {len(techniques)} Techniques, {len(case_studies)} Case Studies.")
    except Exception as e:
        logger.error(f"Error fetching MITRE ATLAS data: {e}")

    # 4. NVD CVE & CPE (Keyword based + Latest)
    logger.info("--- [NVD CVE & CPE Ingestion] ---")
    try:
        nvd_fetcher = NVDCVEFetcher()
        all_cves = []
        all_cpes = []
        
        # A. Fetch CVEs by keyword (limit 50 per keyword to avoid API overloading)
        for kw in active_keywords:
            logger.info(f"Querying NVD CVEs for keyword: '{kw}'")
            try:
                cves = nvd_fetcher.fetch(keyword=kw, limit=50)
                all_cves.extend(cves)
                cpes = nvd_fetcher.extract_cpe_models(nvd_fetcher.last_raw_vulnerabilities)
                all_cpes.extend(cpes)
                
                # Prevent aggressive polling
                time.sleep(3)
            except Exception as kw_e:
                logger.error(f"Error querying NVD for keyword '{kw}': {kw_e}")
        
        # B. Fetch Latest CVEs (Last 14 days, limit 100)
        logger.info("Querying NVD for latest CVEs (last 14 days)...")
        try:
            latest_cves = nvd_fetcher.fetch(limit=100)
            all_cves.extend(latest_cves)
            latest_cpes = nvd_fetcher.extract_cpe_models(nvd_fetcher.last_raw_vulnerabilities)
            all_cpes.extend(latest_cpes)
        except Exception as latest_e:
            logger.error(f"Error querying latest NVD CVEs: {latest_e}")

        # Deduplicate & Save CVEs
        if all_cves:
            storage.save_cves(all_cves)
            stats["nvd_cves"] = len(all_cves)
            for item in all_cves:
                collected_cve_ids.add(item.cve_id)
        
        # Deduplicate & Save CPEs
        if all_cpes:
            storage.save_cpe(all_cpes)
            stats["cpes"] = len(all_cpes)
            
        logger.info(f"Processed NVD CVEs: {len(all_cves)} items. Processed CPEs: {len(all_cpes)} items.")
    except Exception as e:
        logger.error(f"General error during NVD CVE/CPE ingestion: {e}")

    # 5. arXiv (Keyword based)
    logger.info("--- [arXiv Ingestion] ---")
    try:
        arxiv_fetcher = ArXivFetcher()
        all_papers = []
        
        for kw in active_keywords:
            query = f'all:"{kw}"'
            logger.info(f"Querying arXiv for: {query}")
            try:
                papers = arxiv_fetcher.fetch(query=query, limit=20)
                all_papers.extend(papers)
                time.sleep(2)
            except Exception as kw_e:
                logger.error(f"Error querying arXiv for keyword '{kw}': {kw_e}")
                
        if all_papers:
            # Save and deduplicate (deduplication handled by storage.py)
            storage.save_arxiv(all_papers)
            stats["arxiv_papers"] = len(all_papers)
            
        logger.info(f"Processed arXiv papers: {len(all_papers)} items.")
    except Exception as e:
        logger.error(f"General error during arXiv ingestion: {e}")

    # 6. GitHub Repositories (Product based + Search)
    logger.info("--- [GitHub Repository Ingestion] ---")
    try:
        github_fetcher = GitHubRepoFetcher()
        all_repos = []
        
        for prod in active_products:
            # 1. Fetch by Owner/Repo if vendor looks like a Github organization/user
            repo_name = f"{prod.vendor}/{prod.product_name}"
            logger.info(f"Fetching GitHub Repository details for: '{repo_name}'")
            try:
                repo = github_fetcher.fetch_repo_details(repo_name)
                if repo:
                    all_repos.append(repo)
            except Exception as repo_e:
                logger.warning(f"Could not fetch direct repo details for '{repo_name}': {repo_e}")
            
            # 2. Search GitHub for the product to capture related tools
            logger.info(f"Searching GitHub for product query: '{prod.product_name}'")
            try:
                search_results = github_fetcher.search_repositories(prod.product_name, limit=5)
                all_repos.extend(search_results)
                time.sleep(2)
            except Exception as search_e:
                logger.error(f"Error searching GitHub for '{prod.product_name}': {search_e}")
                
        if all_repos:
            storage.save_github(all_repos)
            stats["github_repos"] = len(all_repos)
            
        logger.info(f"Processed GitHub Repositories: {len(all_repos)} items.")
    except Exception as e:
        logger.error(f"General error during GitHub Repository ingestion: {e}")

    # 7. GitHub Security Advisory (GHSA)
    logger.info("--- [GitHub Security Advisory (GHSA) Ingestion] ---")
    try:
        ghsa_fetcher = GitHubAdvisoryFetcher()
        # Fetch latest advisories and filter them using our active products
        ghsa_results = ghsa_fetcher.fetch(limit=100, ai_products=active_products)
        if ghsa_results:
            storage.save_ghsa(ghsa_results)
            stats["ghsa_advisories"] = len(ghsa_results)
            # Add CVE IDs to list for EPSS/CWE query
            for item in ghsa_results:
                if item.cve_id:
                    collected_cve_ids.add(item.cve_id)
            logger.info(f"Fetched and stored {len(ghsa_results)} GHSA items matching active AI products.")
    except Exception as e:
        logger.error(f"Error fetching GitHub Security Advisories: {e}")

    # 8. Dependency Resolution: FIRST EPSS Scores (Based on collected CVE IDs)
    logger.info("--- [FIRST EPSS Score Ingestion] ---")
    if collected_cve_ids:
        try:
            epss_fetcher = FIRSTEPSSFetcher()
            # Convert set to sorted list
            cve_list = sorted(list(collected_cve_ids))
            logger.info(f"Requesting EPSS scores for {len(cve_list)} unique CVEs collected during this run...")
            
            # EPSS API endpoint has limits on URI size, request in chunks if too large
            chunk_size = 50
            all_epss = []
            for i in range(0, len(cve_list), chunk_size):
                chunk = cve_list[i:i + chunk_size]
                logger.info(f"Requesting EPSS chunk {i//chunk_size + 1}/{((len(cve_list)-1)//chunk_size) + 1}")
                try:
                    epss_results = epss_fetcher.fetch(cve_ids=chunk)
                    all_epss.extend(epss_results)
                    time.sleep(1)
                except Exception as chunk_e:
                    logger.error(f"Error fetching EPSS chunk: {chunk_e}")
                    
            if all_epss:
                storage.save_epss(all_epss)
                stats["epss_scores"] = len(all_epss)
                logger.info(f"Successfully stored {len(all_epss)} EPSS scores.")
        except Exception as e:
            logger.error(f"General error during EPSS ingestion: {e}")
    else:
        logger.info("No CVEs collected in this run. Skipping EPSS fetch.")

    # 9. Dependency Resolution: MITRE CWE Details (Based on collected CWE IDs)
    logger.info("--- [MITRE CWE Details Ingestion] ---")
    try:
        # Load accumulated CVEs to extract all CWE IDs
        cves_in_storage = storage.load_cves()
        cwe_ids_to_fetch = set()
        for cve in cves_in_storage:
            for cwe in cve.cwe_ids:
                cwe_ids_to_fetch.add(cwe)
                
        # Load already resolved CWEs from storage to skip them
        existing_cwes = storage.load_cwe()
        resolved_cwe_ids = {c.cwe_id for c in existing_cwes}
        
        # Only fetch CWEs we don't have details for yet
        new_cwe_ids = [cwe for cwe in cwe_ids_to_fetch if cwe not in resolved_cwe_ids]
        
        if new_cwe_ids:
            cwe_list = sorted(new_cwe_ids)
            logger.info(f"Identified {len(cwe_list)} new unique CWE IDs to fetch. Fetching details...")
            cwe_fetcher = CWEFetcher()
            cwe_results = cwe_fetcher.fetch(cwe_list)
            if cwe_results:
                storage.save_cwe(cwe_results)
                stats["cwes"] = len(cwe_results)
                logger.info(f"Successfully stored {len(cwe_results)} new CWE definition models.")
        else:
            logger.info("No new CWE IDs to resolve. Skipping CWE fetch.")
    except Exception as e:
        logger.error(f"Error resolving CWE details: {e}")

    # 10. RSS Feeds Crawl
    logger.info("--- [RSS Feed Crawler] ---")
    try:
        rss_fetcher = RSSFetcher()
        # Fetch RSS feeds from sources configured in Notion (or mock fallback)
        articles, news = rss_fetcher.fetch(sources)
        
        if articles:
            storage.save_articles(articles)
            stats["rss_articles"] = len(articles)
        if news:
            storage.save_news(news)
            stats["rss_news"] = len(news)
            
        logger.info(f"Processed RSS Crawler: {len(articles)} Articles, {len(news)} News items.")
    except Exception as e:
        logger.error(f"Error executing RSS crawl: {e}")

    # --- Summary ---
    logger.info("==================================================")
    logger.info("  Security-for-AI-Monitor Pipeline Run Summary   ")
    logger.info("==================================================")
    logger.info(f"Notion Configuration Access:   {'SUCCESSFUL' if notion_success else 'FAILED (Fallback Used)'}")
    logger.info(f"Notion Sources Configured:     {stats['notion_sources']}")
    logger.info(f"Notion Keywords Configured:    {stats['notion_keywords']}")
    logger.info(f"Notion Products Configured:    {stats['notion_products']}")
    logger.info(f"CISA KEV Vulnerabilities:      {stats['cisa_kev']}")
    logger.info(f"MITRE ATLAS Tactics:           {stats['mitre_atlas_tactics']}")
    logger.info(f"MITRE ATLAS Techniques:        {stats['mitre_atlas_techniques']}")
    logger.info(f"MITRE ATLAS Case Studies:      {stats['mitre_atlas_case_studies']}")
    logger.info(f"NVD CVEs Fetched:              {stats['nvd_cves']}")
    logger.info(f"CPEs Extracted:                {stats['cpes']}")
    logger.info(f"arXiv Papers Fetched:          {stats['arxiv_papers']}")
    logger.info(f"GitHub Repositories Fetched:   {stats['github_repos']}")
    logger.info(f"GitHub Security Advisories:    {stats['ghsa_advisories']}")
    logger.info(f"EPSS Scores Fetched:           {stats['epss_scores']}")
    logger.info(f"CWEs Resolved:                 {stats['cwes']}")
    logger.info(f"RSS Articles Parsed:           {stats['rss_articles']}")
    logger.info(f"RSS News Parsed:               {stats['rss_news']}")
    logger.info("==================================================")
    logger.info("Pipeline Execution Completed Successfully.")


if __name__ == "__main__":
    run_pipeline()
