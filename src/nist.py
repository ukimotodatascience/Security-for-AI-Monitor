from typing import List
from src.base_fetcher import BaseFetcher
from src.models import NISTModel

# Mapping of NIST AI RMF Category IDs to their official names (Core Taxonomy)
NIST_CATEGORIES = {
    "GOVERN-1": "Policies, processes, procedures, and practices are in place, transparent, and implemented effectively.",
    "GOVERN-2": "Accountability structures are established so that appropriate teams/individuals are empowered and trained.",
    "GOVERN-3": "Workforce diversity, equity, inclusion, and accessibility are prioritized in AI risk activities.",
    "GOVERN-4": "Organizational teams are committed to a culture that considers and communicates AI risk.",
    "GOVERN-5": "Processes are in place for robust engagement with relevant AI actors.",
    "GOVERN-6": "Policies and procedures address AI risks and benefits arising from third-party software, data, and supply chain issues.",
    "MAP-1": "Context is established and understood.",
    "MAP-2": "Categorization of the AI system is performed.",
    "MAP-3": "AI capabilities, targeted usage, goals, and expected benefits/costs are understood.",
    "MAP-4": "Risks and benefits are mapped for all components, including third-party software and data.",
    "MAP-5": "Impacts to individuals, groups, communities, organizations, and society are characterized.",
    "MEASURE-1": "Appropriate methods and metrics are identified and applied.",
    "MEASURE-2": "AI systems are evaluated for trustworthy characteristics.",
    "MEASURE-3": "Mechanisms for tracking identified AI risks over time are in place.",
    "MEASURE-4": "Feedback about the efficacy of measurement is gathered and assessed.",
    "MANAGE-1": "AI risks are prioritized, responded to, and managed based on assessments and analysis.",
    "MANAGE-2": "Strategies to maximize benefits and minimize negative impacts are planned, implemented, and documented.",
    "MANAGE-3": "Risks and benefits from third-party entities are managed.",
    "MANAGE-4": "Risk treatments, including response and recovery, and communication plans for the identified and measured AI risks are documented and monitored regularly.",
}


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
                self.logger.info(
                    f"Successfully fetched {len(raw_data)} raw playbook entries."
                )

                nist_models = []
                for item in raw_data:
                    title = item.get("title", "")
                    # Normalize control_id (e.g., "GOVERN 1.1" -> "GOVERN-1.1")
                    control_id = title.replace(" ", "-") if title else "UNKNOWN-ID"

                    func_name = item.get("type", "UNKNOWN")
                    category_id = item.get("category", "UNKNOWN")

                    # Resolve human-readable category name from ID
                    category_name = NIST_CATEGORIES.get(category_id, category_id)

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
                    description = (
                        "\n\n".join(desc_parts)
                        if desc_parts
                        else "No description available."
                    )

                    model = NISTModel(
                        control_id=control_id,
                        function=func_name,
                        category=category_name,
                        subcategory=subcategory,
                        description=description,
                        section_about=section_about if section_about else None,
                        section_actions=section_actions if section_actions else None,
                        section_doc=item.get("section_doc"),
                        section_ref=item.get("section_ref"),
                        ai_actors=item.get("AI Actors", []),
                        topics=item.get("Topic", []),
                    )
                    nist_models.append(model)

                self.logger.info(
                    f"Successfully parsed {len(nist_models)} NISTModel entries."
                )
                return nist_models

        except Exception as e:
            self.logger.error(f"Error fetching or parsing NIST Playbook: {e}")
            raise e
