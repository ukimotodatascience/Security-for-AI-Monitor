from typing import List
from src.base_fetcher import BaseFetcher
from src.models import NISTModel


class NISTPlaybookFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("NISTPlaybookFetcher")
        self.url = "https://airc.nist.gov/docs/playbook.json"

    def fetch(self, **kwargs) -> List[NISTModel]:
        """Fetches the NIST AI RMF Playbook from the official AIRC endpoint
        and parses it into a list of NISTModel objects.
        """
        self.logger.info(f"Fetching NIST AI RMF Playbook from {self.url}...")
        
        try:
            with self._get_client() as client:
                response = client.get(self.url)
                if response.status_code != 200:
                    raise Exception(
                        f"Failed to fetch NIST Playbook. Status code: {response.status_code}"
                    )
                
                raw_data = response.json()
                self.logger.info(f"Successfully fetched {len(raw_data)} raw playbook entries.")
                
                nist_models = []
                for item in raw_data:
                    title = item.get("title", "")
                    # Normalize control_id (e.g., "GOVERN 1.1" -> "GOVERN-1.1")
                    control_id = title.replace(" ", "-") if title else "UNKNOWN-ID"
                    
                    func_name = item.get("type", "UNKNOWN")
                    category = item.get("category", "UNKNOWN")
                    
                    # Subcategory is the summary requirement description
                    subcategory = item.get("description", "")
                    
                    # Merge detailed sections for the main 'description' field
                    section_about = item.get("section_about", "")
                    section_actions = item.get("section_actions", "")
                    desc_parts = []
                    if section_about:
                        desc_parts.append(f"About:\n{section_about}")
                    if section_actions:
                        desc_parts.append(f"Actions:\n{section_actions}")
                    description = "\n\n".join(desc_parts) if desc_parts else "No description available."
                    
                    model = NISTModel(
                        control_id=control_id,
                        function=func_name,
                        category=category,
                        subcategory=subcategory,
                        description=description,
                        section_about=section_about if section_about else None,
                        section_actions=section_actions if section_actions else None,
                        section_doc=item.get("section_doc"),
                        section_ref=item.get("section_ref"),
                        ai_actors=item.get("AI Actors", []),
                        topics=item.get("Topic", [])
                    )
                    nist_models.append(model)
                
                self.logger.info(f"Successfully parsed {len(nist_models)} NISTModel entries.")
                return nist_models
                
        except Exception as e:
            self.logger.error(f"Error fetching or parsing NIST Playbook: {e}")
            raise e
