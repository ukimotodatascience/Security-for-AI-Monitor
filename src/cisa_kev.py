from typing import List
from src.base_fetcher import BaseFetcher
from src.config import Config
from src.models import KEVModel

class CISAKEVFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("CISAKEVFetcher")
        self.url = Config.KEV_FEED_URL

    def fetch(self, **kwargs) -> List[KEVModel]:
        """Fetch KEV vulnerabilities from CISA JSON feed."""
        self.logger.info(f"Fetching CISA KEV from {self.url}...")
        
        with self._get_client() as client:
            response = client.get(self.url)
            response.raise_for_status()
            data = response.json()

        vulnerabilities = data.get("vulnerabilities", [])
        self.logger.info(f"Fetched {len(vulnerabilities)} raw vulnerabilities from CISA KEV.")

        results = []
        for v in vulnerabilities:
            try:
                # Map API field names to KEVModel (which uses table schema names)
                model = KEVModel(
                    cve_id=v.get("cveID"),
                    product=v.get("product", ""),
                    vulnerability_name=v.get("vulnerabilityName", ""),
                    added_date=v.get("dateAdded"),
                    due_date=v.get("dueDate"),
                    known_ransomware_campaign_use=v.get("knownRansomwareCampaignUse", "Unknown"),
                    required_action=v.get("requiredAction", ""),
                    notes=v.get("notes")
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse vulnerability {v.get('cveID')}: {e}")
                
        self.logger.info(f"Successfully parsed {len(results)} KEV models.")
        return results
