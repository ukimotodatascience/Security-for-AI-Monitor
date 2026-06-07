import yaml
from typing import Dict, List, Tuple
from src.base_fetcher import BaseFetcher
from src.models import ATLASTacticModel, ATLASTechniqueModel, ATLASCaseStudyModel


class ATLASFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("ATLASFetcher")
        self.latest_meta_url = "https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/v6/ATLAS-latest.yaml"
        self.base_v6_url = (
            "https://raw.githubusercontent.com/mitre-atlas/atlas-data/main/dist/v6/"
        )

    def fetch(
        self, **kwargs
    ) -> Tuple[
        List[ATLASTacticModel], List[ATLASTechniqueModel], List[ATLASCaseStudyModel]
    ]:
        """Fetch latest ATLAS v6 data, parse tactics, techniques, and case studies.

        Returns:
            Tuple containing:
            - List[ATLASTacticModel]
            - List[ATLASTechniqueModel]
            - List[ATLASCaseStudyModel]
        """
        self.logger.info(
            f"Resolving latest ATLAS v6 filename from {self.latest_meta_url}..."
        )
        with self._get_client() as client:
            res = client.get(self.latest_meta_url)
            res.raise_for_status()
            latest_filename = res.text.strip()

            yaml_url = f"{self.base_v6_url}{latest_filename}"
            self.logger.info(f"Fetching MITRE ATLAS v6 data from {yaml_url}...")
            response = client.get(yaml_url)
            response.raise_for_status()
            yaml_content = response.text

        self.logger.info("Parsing ATLAS v6 YAML data...")
        doc = yaml.safe_load(yaml_content)

        raw_tactics = doc.get("tactics", {})
        raw_techniques = doc.get("techniques", {})
        raw_mitigations = doc.get("mitigations", {})
        raw_case_studies = doc.get("case-studies", {})
        relationships = doc.get("relationships", {})

        # 1. Map technique ID -> mitigations (derived from mitigations relationships)
        tech_to_mitigations: Dict[str, List[str]] = {}
        for m_id, mit in raw_mitigations.items():
            mit_name = mit.get("name", "")
            rel = relationships.get(m_id, {})
            for mit_rel in rel.get("mitigates", []):
                t_id = mit_rel.get("target")
                if t_id:
                    if t_id not in tech_to_mitigations:
                        tech_to_mitigations[t_id] = []
                    if mit_name not in tech_to_mitigations[t_id]:
                        tech_to_mitigations[t_id].append(mit_name)

        # 2. Map technique ID -> case study names (derived from case studies relationships)
        tech_to_examples: Dict[str, List[str]] = {}
        parsed_case_studies: List[ATLASCaseStudyModel] = []

        for cs_id, cs in raw_case_studies.items():
            cs_name = cs.get("name", "")
            summary = cs.get("summary") or cs.get("description", "")

            # Extract related techniques from employs relationship
            related_techs = []
            rel = relationships.get(cs_id, {})
            for emp_rel in rel.get("employs", []):
                t_id = emp_rel.get("target")
                if t_id:
                    related_techs.append(t_id)
                    if t_id not in tech_to_examples:
                        tech_to_examples[t_id] = []
                    if cs_name not in tech_to_examples[t_id]:
                        tech_to_examples[t_id].append(cs_name)

            related_techs = list(set(related_techs))
            url = f"https://atlas.mitre.org/studies/{cs_id}"

            case_model = ATLASCaseStudyModel(
                case_id=cs_id,
                title=cs_name,
                summary=summary,
                related_techniques=related_techs,
                url=url,
            )
            parsed_case_studies.append(case_model)

        # 3. Map technique ID -> tactic ID (derived from achieves and employs relationships)
        tech_to_tactic: Dict[str, str] = {}
        for source_id, rels in relationships.items():
            if source_id.startswith("AML.T"):
                for ach in rels.get("achieves", []):
                    tgt = ach.get("target")
                    if tgt and tgt.startswith("AML.TA"):
                        tech_to_tactic[source_id] = tgt

        for source_id, rels in relationships.items():
            for emp in rels.get("employs", []):
                tgt = emp.get("target")
                tactic = emp.get("tactic")
                if (
                    tgt
                    and tgt.startswith("AML.T")
                    and tactic
                    and tactic.startswith("AML.TA")
                ):
                    if tgt not in tech_to_tactic:
                        tech_to_tactic[tgt] = tactic

        # 4. Parse Tactics
        parsed_tactics: List[ATLASTacticModel] = []
        for t_id, tac in raw_tactics.items():
            name = tac.get("name", "")
            desc = tac.get("description", "")
            parsed_tactics.append(
                ATLASTacticModel(tactic_id=t_id, name=name, description=desc)
            )

        # 5. Parse Techniques
        parsed_techniques: List[ATLASTechniqueModel] = []
        for tech_id, tech in raw_techniques.items():
            name = tech.get("name", "")
            desc = tech.get("description", "")

            # Get tactic ID from achieves or employs relationship map
            tactic_id = tech_to_tactic.get(tech_id, "")

            mitigations = tech_to_mitigations.get(tech_id, [])
            examples = tech_to_examples.get(tech_id, [])

            parsed_techniques.append(
                ATLASTechniqueModel(
                    technique_id=tech_id,
                    tactic_id=tactic_id,
                    name=name,
                    description=desc,
                    mitigations=mitigations,
                    examples=examples,
                )
            )

        self.logger.info(
            f"Successfully parsed {len(parsed_tactics)} Tactics, "
            f"{len(parsed_techniques)} Techniques, and "
            f"{len(parsed_case_studies)} Case Studies from ATLAS v6."
        )

        return parsed_tactics, parsed_techniques, parsed_case_studies
