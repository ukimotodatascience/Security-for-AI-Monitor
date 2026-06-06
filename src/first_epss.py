from typing import List
from src.base_fetcher import BaseFetcher
from src.config import Config
from src.models import EPSSModel

class FIRSTEPSSFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("FIRSTEPSSFetcher")
        self.url = Config.EPSS_API_URL

    def fetch(self, cve_ids: List[str] = None, **kwargs) -> List[EPSSModel]:
        """Fetch EPSS scores for given CVE IDs.
        
        If cve_ids is empty or not provided, fetch the top/latest records (limited by API).
        """
        params = {}
        if cve_ids:
            # EPSS API supports comma-separated CVEs
            params["cve"] = ",".join(cve_ids)
            self.logger.info(f"Fetching EPSS scores for {len(cve_ids)} CVEs from {self.url}...")
        else:
            self.logger.info(f"Fetching latest EPSS scores from {self.url}...")

        with self._get_client() as client:
            response = client.get(self.url, params=params)
            response.raise_for_status()
            data = response.json()

        records = data.get("data", [])
        # The response format could be a list of dicts, or a dict keyed by CVE.
        # According to FIRST EPSS API, the 'data' field is a list:
        # [{"cve": "CVE-...", "epss": "0.05", "percentile": "0.80", "date": "2026-06-06"}]
        self.logger.info(f"Fetched {len(records)} EPSS records.")

        results = []
        # If records is a dict, convert it to a list
        if isinstance(records, dict):
            # Sometimes 'data' is returned as { "CVE-xxx": { "epss": "...", "percentile": "..." } }
            records_list = []
            for cve, details in records.items():
                details["cve"] = cve
                records_list.append(details)
            records = records_list

        for r in records:
            try:
                # FIRST API returns epss and percentile as strings, Pydantic will cast them to float/int
                model = EPSSModel(
                    cve_id=r.get("cve"),
                    epss=float(r.get("epss", 0.0)),
                    percentile=float(r.get("percentile", 0.0)),
                    date=r.get("date")
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse EPSS record {r}: {e}")

        self.logger.info(f"Successfully parsed {len(results)} EPSS models.")
        return results
