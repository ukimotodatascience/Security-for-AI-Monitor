from datetime import datetime
from typing import List, Optional
from src.base_fetcher import BaseFetcher
from src.config import Config
from src.models import CVEModel

class NVDCVEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("NVDCVEFetcher")
        self.url = Config.NVD_API_URL
        if Config.NVD_API_KEY:
            self.headers["apiKey"] = Config.NVD_API_KEY

    def fetch(self, keyword: Optional[str] = None, limit: int = 20, **kwargs) -> List[CVEModel]:
        """Fetch CVEs from NVD API.
        
        Optional search criteria:
        - keyword: search string in descriptions (e.g. "prompt injection" or "langchain")
        - limit: number of results to fetch (resultsPerPage)
        """
        params = {"resultsPerPage": min(limit, 2000)}
        if keyword:
            params["keywordSearch"] = keyword
            self.logger.info(f"Fetching CVEs matching keyword '{keyword}' from {self.url}...")
        else:
            self.logger.info(f"Fetching latest CVEs from {self.url}...")

        with self._get_client() as client:
            response = client.get(self.url, params=params)
            response.raise_for_status()
            data = response.json()

        vulnerabilities = data.get("vulnerabilities", [])
        self.logger.info(f"Fetched {len(vulnerabilities)} raw CVEs from NVD API.")

        results = []
        for vuln in vulnerabilities:
            cve_data = vuln.get("cve", {})
            cve_id = cve_data.get("id")
            if not cve_id:
                continue

            try:
                # 1. Get English description
                descriptions = cve_data.get("descriptions", [])
                desc_text = ""
                for desc in descriptions:
                    if desc.get("lang") == "en":
                        desc_text = desc.get("value", "")
                        break
                if not desc_text and descriptions:
                    desc_text = descriptions[0].get("value", "")

                # 2. Extract CVSS info (look for V3.1, V3.0, or V4.0, fallback to V2)
                metrics = cve_data.get("metrics", {})
                cvss_version = None
                cvss_base_score = None
                cvss_base_label = None

                # Check CVSS V4.0
                if "cvssMetricV40" in metrics and metrics["cvssMetricV40"]:
                    cvss = metrics["cvssMetricV40"][0].get("cvssData", {})
                    cvss_version = "v4.0"
                    cvss_base_score = cvss.get("baseScore")
                    cvss_base_label = cvss.get("baseSeverity")
                # Check CVSS V3.1
                elif "cvssMetricV31" in metrics and metrics["cvssMetricV31"]:
                    cvss = metrics["cvssMetricV31"][0].get("cvssData", {})
                    cvss_version = "v3.1"
                    cvss_base_score = cvss.get("baseScore")
                    cvss_base_label = cvss.get("baseSeverity")
                # Check CVSS V3.0
                elif "cvssMetricV30" in metrics and metrics["cvssMetricV30"]:
                    cvss = metrics["cvssMetricV30"][0].get("cvssData", {})
                    cvss_version = "v3.0"
                    cvss_base_score = cvss.get("baseScore")
                    cvss_base_label = cvss.get("baseSeverity")
                # Check CVSS V2
                elif "cvssMetricV2" in metrics and metrics["cvssMetricV2"]:
                    cvss = metrics["cvssMetricV2"][0].get("cvssData", {})
                    cvss_version = "v2.0"
                    cvss_base_score = cvss.get("baseScore")
                    cvss_base_label = metrics["cvssMetricV2"][0].get("baseSeverity")

                # 3. Extract CWE IDs
                weaknesses = cve_data.get("weaknesses", [])
                cwe_ids = []
                for w in weaknesses:
                    desc_list = w.get("description", [])
                    for d in desc_list:
                        val = d.get("value", "")
                        if val.startswith("CWE-"):
                            cwe_ids.append(val)

                # 4. Extract CPE Names
                configurations = cve_data.get("configurations", [])
                cpe_names = []
                for config in configurations:
                    nodes = config.get("nodes", [])
                    for node in nodes:
                        cpe_matches = node.get("cpeMatch", [])
                        for match in cpe_matches:
                            criteria = match.get("criteria")
                            if criteria:
                                cpe_names.append(criteria)

                model = CVEModel(
                    cve_id=cve_id,
                    published_at=cve_data.get("published"),
                    last_modified_at=cve_data.get("lastModified"),
                    description=desc_text,
                    cvss_version=cvss_version,
                    cvss_base_score=cvss_base_score,
                    cvss_base_label=cvss_base_label,
                    cwe_ids=cwe_ids,
                    cpe_names=cpe_names
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse CVE {cve_id}: {e}")

        self.logger.info(f"Successfully parsed {len(results)} CVE models.")
        return results
