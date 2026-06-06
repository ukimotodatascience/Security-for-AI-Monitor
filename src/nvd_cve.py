from datetime import datetime, timedelta, timezone
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

    def fetch(
        self,
        keyword: Optional[str] = None,
        limit: int = 20,
        pub_start_date: Optional[datetime] = None,
        pub_end_date: Optional[datetime] = None,
        days_ago: Optional[int] = None,
        **kwargs,
    ) -> List[CVEModel]:
        """Fetch CVEs from NVD API.

        Optional search criteria:
        - keyword: search string in descriptions (e.g. "prompt injection" or "langchain")
        - limit: number of results to fetch (resultsPerPage)
        - pub_start_date: filter by publish start date
        - pub_end_date: filter by publish end date
        - days_ago: filter by publish date within the last N days (e.g. 14)
        """
        params = {"resultsPerPage": min(limit, 2000)}

        # Normalize input dates to timezone-aware (UTC)
        if pub_start_date is not None:
            if pub_start_date.tzinfo is None:
                pub_start_date = pub_start_date.replace(tzinfo=timezone.utc)
            else:
                pub_start_date = pub_start_date.astimezone(timezone.utc)
        if pub_end_date is not None:
            if pub_end_date.tzinfo is None:
                pub_end_date = pub_end_date.replace(tzinfo=timezone.utc)
            else:
                pub_end_date = pub_end_date.astimezone(timezone.utc)

        # Calculate dates if days_ago is specified
        if days_ago is not None:
            pub_end_date = datetime.now(timezone.utc)
            pub_start_date = pub_end_date - timedelta(days=days_ago)
        # Fallback default date range if no keyword and no date filter is provided
        elif keyword is None and pub_start_date is None and pub_end_date is None:
            # Default to last 14 days to retrieve actually recent CVEs
            pub_end_date = datetime.now(timezone.utc)
            pub_start_date = pub_end_date - timedelta(days=14)

        # Complement dates if only one boundary is specified (NVD API requires both)
        if (pub_start_date is not None and pub_end_date is None) or (
            pub_end_date is not None and pub_start_date is None
        ):
            if pub_start_date is not None:
                pub_end_date = min(
                    pub_start_date + timedelta(days=120), datetime.now(timezone.utc)
                )
            else:
                pub_start_date = pub_end_date - timedelta(days=120)

        # Validate publication date bounds if both are specified
        if pub_start_date is not None and pub_end_date is not None:
            if pub_start_date > pub_end_date:
                raise ValueError("pub_start_date cannot be after pub_end_date")
            if pub_end_date - pub_start_date > timedelta(days=120):
                raise ValueError(
                    "The date range for NVD publication filter cannot exceed 120 days."
                )

        if pub_start_date:
            params["pubStartDate"] = pub_start_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        if pub_end_date:
            params["pubEndDate"] = pub_end_date.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if keyword:
            params["keywordSearch"] = keyword
            self.logger.info(
                f"Fetching CVEs matching keyword '{keyword}' from {self.url}..."
            )
        else:
            self.logger.info(
                f"Fetching latest CVEs from {self.url} between {params.get('pubStartDate')} and {params.get('pubEndDate')}..."
            )

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

                def extract_cpes(node_list: list):
                    for node in node_list:
                        cpe_matches = node.get("cpeMatch", [])
                        for match in cpe_matches:
                            criteria = match.get("criteria")
                            if criteria:
                                cpe_names.append(criteria)

                        # Recurse into nested children nodes
                        children = node.get("children", [])
                        if children:
                            extract_cpes(children)

                for config in configurations:
                    nodes = config.get("nodes", [])
                    extract_cpes(nodes)

                model = CVEModel(
                    cve_id=cve_id,
                    published_at=cve_data.get("published"),
                    last_modified_at=cve_data.get("lastModified"),
                    description=desc_text,
                    cvss_version=cvss_version,
                    cvss_base_score=cvss_base_score,
                    cvss_base_label=cvss_base_label,
                    cwe_ids=cwe_ids,
                    cpe_names=cpe_names,
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse CVE {cve_id}: {e}")

        self.logger.info(f"Successfully parsed {len(results)} CVE models.")
        return results
