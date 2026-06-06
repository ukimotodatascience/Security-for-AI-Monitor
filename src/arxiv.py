import urllib.parse
from typing import List, Optional
import httpx
import xmltodict
from src.base_fetcher import BaseFetcher
from src.config import Config
from src.models import ArXivModel

class ArXivFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("ArXivFetcher")
        self.url = Config.ARXIV_API_URL

    def fetch(self, query: str = 'all:"AI security" OR all:"prompt injection"', limit: int = 10, **kwargs) -> List[ArXivModel]:
        """Fetch papers from arXiv API.
        
        Args:
            query: search query string (e.g. 'all:"prompt injection"')
            limit: maximum number of papers to fetch
        """
        params = {
            "search_query": query,
            "max_results": limit,
            "sortBy": "submittedDate",
            "sortOrder": "descending"
        }
        
        # urllib.parse.urlencode manually to keep the query string structure clean
        encoded_params = urllib.parse.urlencode(params)
        full_url = f"{self.url}?{encoded_params}"
        
        self.logger.info(f"Fetching papers from arXiv with query '{query}' (URL: {full_url})...")
        
        try:
            with httpx.Client(headers=self.headers, timeout=10.0, follow_redirects=True) as client:
                response = client.get(full_url)
                response.raise_for_status()
                xml_data = response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch data from arXiv due to error: {e}")
            return []

        # Parse XML to dict using xmltodict
        parsed_dict = xmltodict.parse(xml_data)
        feed = parsed_dict.get("feed", {})
        entries = feed.get("entry", [])

        # Ensure entries is a list
        if isinstance(entries, dict):
            entries = [entries]
        elif not entries:
            entries = []

        self.logger.info(f"Fetched {len(entries)} entries from arXiv.")

        results = []
        for entry in entries:
            try:
                # 1. Parse arxiv_id
                # entry['id'] is typically "http://arxiv.org/abs/2501.01234v1"
                raw_id = entry.get("id", "")
                arxiv_id = raw_id.split("/abs/")[-1] if "/abs/" in raw_id else raw_id

                # 2. Parse title and summary
                title = entry.get("title", "").replace("\n", " ").strip()
                summary = entry.get("summary", "").replace("\n", " ").strip()

                # 3. Parse authors
                authors_raw = entry.get("author", [])
                if isinstance(authors_raw, dict):
                    authors = [authors_raw.get("name", "")]
                elif isinstance(authors_raw, list):
                    authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]
                else:
                    authors = []

                # 4. Parse categories
                categories_raw = entry.get("category", [])
                if isinstance(categories_raw, dict):
                    categories = [categories_raw.get("@term", "")]
                elif isinstance(categories_raw, list):
                    categories = [c.get("@term", "") for c in categories_raw if isinstance(c, dict)]
                else:
                    categories = []

                # 5. Parse links
                links = entry.get("link", [])
                if isinstance(links, dict):
                    links = [links]
                
                pdf_url = ""
                abs_url = raw_id # default to raw id
                
                for link in links:
                    if not isinstance(link, dict):
                        continue
                    rel = link.get("@rel")
                    title_attr = link.get("@title")
                    href = link.get("@href", "")
                    
                    if rel == "alternate":
                        abs_url = href
                    elif rel == "related" and title_attr == "pdf":
                        pdf_url = href

                # If pdf_url is empty but we have abs_url, we can construct pdf_url as fallback
                if not pdf_url and "/abs/" in abs_url:
                    pdf_url = abs_url.replace("/abs/", "/pdf/") + ".pdf"

                # 6. Map to ArXivModel (remaining fields like keywords_matched, mappings can be processed downstream)
                model = ArXivModel(
                    arxiv_id=arxiv_id,
                    title=title,
                    authors=authors,
                    summary=summary,
                    published_at=entry.get("published"),
                    updated_at=entry.get("updated"),
                    categories=categories,
                    pdf_url=pdf_url,
                    abs_url=abs_url,
                    keywords_matched=[], # Will be processed by downstream classifier
                    owasp_mapping=[],
                    mitre_mapping=[],
                    importance_score=None
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse arXiv entry {entry.get('id')}: {e}")

        self.logger.info(f"Successfully parsed {len(results)} ArXiv models.")
        return results
