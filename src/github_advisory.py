from typing import List, Optional
from src.base_fetcher import BaseFetcher
from src.models import GHSAModel, AIProductModel


class GitHubAdvisoryFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("GitHubAdvisoryFetcher")
        self.url = "https://api.github.com/advisories"
        # Set User-Agent as required by GitHub API
        self.headers["User-Agent"] = "Security-for-AI-Monitor/1.0"
        self.headers["Accept"] = "application/vnd.github+json"

    def fetch(
        self,
        limit: int = 50,
        ai_products: Optional[List[AIProductModel]] = None,
        **kwargs,
    ) -> List[GHSAModel]:
        """Fetch latest security advisories from GitHub and filter them for AI products.

        Args:
            limit: Maximum number of advisories to fetch.
            ai_products: Optional list of AIProductModel to filter against. If not provided,
                          we search for typical AI package keywords.

        Returns:
            List of GHSAModel objects matching AI-related criteria.
        """
        params = {"per_page": min(limit, 100), "direction": "desc", "sort": "published"}

        self.logger.info(
            f"Fetching latest {params['per_page']} advisories from GitHub API..."
        )
        try:
            with self._get_client() as client:
                response = client.get(self.url, params=params)
                response.raise_for_status()
                advisories = response.json()
        except Exception as e:
            self.logger.error(f"Failed to fetch GitHub advisories: {e}")
            return []

        self.logger.info(
            f"Fetched {len(advisories)} raw advisories. Filtering for AI packages..."
        )

        # Build set of lower-case product names and aliases for filtering
        ai_names = set()
        if ai_products:
            for prod in ai_products:
                ai_names.add(prod.product_name.lower())
                ai_names.add(prod.vendor.lower())
                for alias in prod.aliases:
                    ai_names.add(alias.lower())
        else:
            # Fallback list of common AI/ML packages if no products list provided
            ai_names = {
                "langchain",
                "llama-index",
                "llamaindex",
                "ollama",
                "tensorflow",
                "pytorch",
                "transformers",
                "huggingface",
                "keras",
                "scikit-learn",
                "numpy",
                "pandas",
                "mlflow",
                "ray",
                "boto3",
                "langchain-core",
                "langchain-community",
                "gradio",
                "streamlit",
                "dspy",
                "autogen",
                "crewai",
                "langgraph",
                "fastapi",
            }

        results = []
        for adv in advisories:
            ghsa_id = adv.get("ghsa_id", "")
            if not ghsa_id:
                continue

            summary = adv.get("summary", "")
            description = adv.get("description", "")
            vulnerabilities = adv.get("vulnerabilities", [])

            # Extract package names involved in this advisory
            pkg_names = []
            patched_versions = []
            is_ai_related = False

            for vuln in vulnerabilities:
                pkg = vuln.get("package", {})
                pkg_name = pkg.get("name", "")
                if pkg_name:
                    pkg_names.append(pkg_name)
                    # Check if the package is in our AI products list
                    if pkg_name.lower() in ai_names or any(
                        name in pkg_name.lower() for name in ai_names
                    ):
                        is_ai_related = True

                    p_version = vuln.get("first_patched_version")
                    if p_version:
                        patched_versions.append(p_version)

            # Broaden filter check: also scan summary/description for keywords if packages aren't explicitly AI but text mentions AI keywords
            if not is_ai_related:
                combined_text = f"{summary} {description}".lower()
                ai_keywords = {
                    "prompt injection",
                    "large language model",
                    "llm agent",
                    "neural network",
                    "machine learning",
                }
                if any(kw in combined_text for kw in ai_keywords):
                    # If text matches AI security keywords, we consider it related
                    is_ai_related = True

            if not is_ai_related:
                continue

            # Format fields
            affected_package = ",".join(pkg_names) if pkg_names else "unknown"
            patched_versions_str = (
                ",".join(patched_versions) if patched_versions else None
            )

            # Parse datetime fields
            pub_at = adv.get("published_at")
            up_at = adv.get("updated_at")

            # GHSA Model mapping
            model = GHSAModel(
                advisory_id=ghsa_id,
                ghsa_id=ghsa_id,
                cve_id=adv.get("cve_id"),
                summary=summary,
                severity=adv.get("severity", "unknown"),
                affected_package=affected_package,
                patched_versions=patched_versions_str,
                published_at=pub_at,
                updated_at=up_at,
                url=adv.get("html_url", ""),
            )
            results.append(model)

        self.logger.info(f"Successfully filtered {len(results)} AI-related advisories.")
        return results
