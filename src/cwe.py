from typing import List
from src.base_fetcher import BaseFetcher
from src.models import CWEModel


class CWEFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("CWEFetcher")
        self.base_url = "https://cwe-api.mitre.org/api/v1/cwe/weakness"

    def fetch(self, cwe_ids: List[str]) -> List[CWEModel]:
        """Fetch details for a list of CWE IDs (e.g. ['CWE-79', 'CWE-89']) from MITRE CWE REST API.

        Args:
            cwe_ids: List of CWE identifier strings.

        Returns:
            List of CWEModel objects populated with details.
        """
        if not cwe_ids:
            return []

        # Clean IDs: convert "CWE-79" to "79"
        clean_ids = []
        for cid in cwe_ids:
            cid_str = str(cid).strip().upper()
            if cid_str.startswith("CWE-"):
                clean_ids.append(cid_str[4:])
            else:
                clean_ids.append(cid_str)

        # Unique clean IDs
        clean_ids = list(set(clean_ids))
        if not clean_ids:
            return []

        # API expects comma-separated IDs
        ids_param = ",".join(clean_ids)
        url = f"{self.base_url}/{ids_param}"

        self.logger.info(f"Fetching CWE data for {cwe_ids} from {url}...")
        try:
            with self._get_client() as client:
                response = client.get(url, timeout=15.0)
                response.raise_for_status()
                data = response.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch CWE details: {e}")
            return []

        weaknesses = data.get("Weaknesses", [])
        self.logger.info(f"Fetched {len(weaknesses)} CWEs from API.")

        results = []
        for item in weaknesses:
            raw_id = item.get("ID")
            if not raw_id:
                continue

            cwe_id = f"CWE-{raw_id}"
            model = CWEModel(
                cwe_id=cwe_id,
                name=item.get("Name", ""),
                description=item.get("Description", ""),
                abstraction=item.get("Abstraction", ""),
                status=item.get("Status", ""),
            )
            results.append(model)

        return results
