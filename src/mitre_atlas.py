import httpx
import yaml
from typing import Any, Dict, List, Tuple
from src.base_fetcher import BaseFetcher
from src.models import ATLASTacticModel, ATLASTechniqueModel, ATLASCaseStudyModel


class ATLASFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("ATLASFetcher")
        self.url = "https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/ATLAS.yaml"

    def fetch(self, **kwargs) -> Tuple[List[ATLASTacticModel], List[ATLASTechniqueModel], List[ATLASCaseStudyModel]]:
        """Fetch ATLAS.yaml and parse tactics, techniques, and case studies.

        Returns:
            Tuple containing:
            - List[ATLASTacticModel]
            - List[ATLASTechniqueModel]
            - List[ATLASCaseStudyModel]
        """
        self.logger.info(f"Fetching MITRE ATLAS data from {self.url}...")
        with self._get_client() as client:
            response = client.get(self.url)
            response.raise_for_status()
            yaml_content = response.text

        self.logger.info("Parsing ATLAS YAML data...")
        doc = yaml.safe_load(yaml_content)

        matrix = doc.get("matrices", [{}])[0]
        raw_tactics = matrix.get("tactics", [])
        raw_techniques = matrix.get("techniques", [])
        raw_mitigations = matrix.get("mitigations", [])
        raw_case_studies = doc.get("case-studies", [])

        # 1. Map technique ID -> mitigations (derived from mitigations list)
        tech_to_mitigations: Dict[str, List[str]] = {}
        for mit in raw_mitigations:
            mit_name = mit.get("name", "")
            for t_ref in mit.get("techniques", []):
                t_id = t_ref.get("id")
                if t_id:
                    if t_id not in tech_to_mitigations:
                        tech_to_mitigations[t_id] = []
                    tech_to_mitigations[t_id].append(mit_name)

        # 2. Map technique ID -> case study names (derived from case studies)
        tech_to_examples: Dict[str, List[str]] = {}
        parsed_case_studies: List[ATLASCaseStudyModel] = []

        for cs in raw_case_studies:
            cs_id = cs.get("id", "")
            cs_name = cs.get("name", "")
            summary = cs.get("summary", "")
            
            # Extract related techniques from procedure list
            related_techs = []
            for p in cs.get("procedure", []):
                t_id = p.get("technique")
                if t_id:
                    related_techs.append(t_id)
                    if t_id not in tech_to_examples:
                        tech_to_examples[t_id] = []
                    if cs_name not in tech_to_examples[t_id]:
                        tech_to_examples[t_id].append(cs_name)
            
            # Deduplicate related techniques
            related_techs = list(set(related_techs))
            url = f"https://atlas.mitre.org/studies/{cs_id}"

            case_model = ATLASCaseStudyModel(
                case_id=cs_id,
                title=cs_name,
                summary=summary,
                related_techniques=related_techs,
                url=url
            )
            parsed_case_studies.append(case_model)

        # 3. Parse Tactics
        parsed_tactics: List[ATLASTacticModel] = []
        for tac in raw_tactics:
            t_id = tac.get("id", "")
            name = tac.get("name", "")
            desc = tac.get("description", "")
            parsed_tactics.append(ATLASTacticModel(
                tactic_id=t_id,
                name=name,
                description=desc
            ))

        # 4. Parse Techniques
        parsed_techniques: List[ATLASTechniqueModel] = []
        for tech in raw_techniques:
            tech_id = tech.get("id", "")
            name = tech.get("name", "")
            desc = tech.get("description", "")
            
            # Get first tactic ID
            t_ids = tech.get("tactics", [])
            tactic_id = t_ids[0] if t_ids else ""

            mitigations = tech_to_mitigations.get(tech_id, [])
            examples = tech_to_examples.get(tech_id, [])

            parsed_techniques.append(ATLASTechniqueModel(
                technique_id=tech_id,
                tactic_id=tactic_id,
                name=name,
                description=desc,
                mitigations=mitigations,
                examples=examples
            ))

        self.logger.info(
            f"Successfully parsed {len(parsed_tactics)} Tactics, "
            f"{len(parsed_techniques)} Techniques, and "
            f"{len(parsed_case_studies)} Case Studies."
        )

        return parsed_tactics, parsed_techniques, parsed_case_studies
