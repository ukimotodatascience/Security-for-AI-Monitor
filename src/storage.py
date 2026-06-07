import os
import uuid
import pandas as pd
from typing import List, TypeVar, Type, Union
from pydantic import BaseModel
from filelock import FileLock
from src.models import (
    CVEModel,
    EPSSModel,
    KEVModel,
    ArXivModel,
    GitHubRepoModel,
    NotionSourceModel,
    AIKeywordModel,
    AIProductModel,
    CWEModel,
    CPEModel,
    ATLASTacticModel,
    ATLASTechniqueModel,
    ATLASCaseStudyModel,
    GHSAModel,
    ArticleModel,
    NewsModel,
    NISTModel,
)


T = TypeVar("T", bound=BaseModel)


class FileStorage:
    """Storage class to handle saving and loading Pydantic models to/from Parquet files.

    Performs Upsert operations using defined primary keys to avoid duplicate entries.
    """

    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir

    def _save_models(
        self,
        items: List[T],
        primary_key: Union[str, List[str]],
        folder: str,
        filename: str,
    ) -> None:
        """Saves a list of Pydantic models to a Parquet file, executing an Upsert

        based on the primary key. Acquires a file lock to prevent concurrent write issues.
        """
        if not items:
            return

        # Ensure directory exists
        target_dir = os.path.join(self.base_dir, folder)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{filename}.parquet")

        lock_filepath = f"{filepath}.lock"
        lock = FileLock(lock_filepath)

        with lock:
            # Convert Pydantic models to dictionaries
            # Using model_dump() keeps date/datetime objects, which pandas translates well for Parquet.
            data = [item.model_dump() for item in items]
            new_df = pd.DataFrame(data)

            # Check if existing file exists to merge
            if os.path.exists(filepath):
                existing_df = pd.read_parquet(filepath)
                # Concatenate existing and new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            else:
                combined_df = new_df

            # Remove duplicates based on the primary key, keeping the last (newest) record
            subset = [primary_key] if isinstance(primary_key, str) else primary_key
            combined_df.drop_duplicates(subset=subset, keep="last", inplace=True)

            # Write back to Parquet atomically using a unique temporary file
            temp_filename = f"{filename}.{uuid.uuid4().hex}.tmp"
            temp_filepath = os.path.join(target_dir, temp_filename)
            try:
                combined_df.to_parquet(temp_filepath, index=False)
                os.replace(temp_filepath, filepath)
            except Exception as e:
                # Cleanup temporary file if it exists
                if os.path.exists(temp_filepath):
                    try:
                        os.remove(temp_filepath)
                    except Exception:
                        pass
                raise e

    def _load_models(self, model_class: Type[T], folder: str, filename: str) -> List[T]:
        """Loads a list of Pydantic models from a Parquet file."""
        filepath = os.path.join(self.base_dir, folder, f"{filename}.parquet")
        if not os.path.exists(filepath):
            return []

        df = pd.read_parquet(filepath)
        records = df.to_dict(orient="records")

        # Normalize NaN/NaT values to None and convert arrays to lists to prevent Pydantic validation errors
        cleaned_records = []
        for r in records:
            cleaned_r = {}
            for k, v in r.items():
                if isinstance(v, (list, dict)):
                    cleaned_r[k] = v
                elif hasattr(v, "__len__") and not isinstance(v, (str, bytes)):
                    # Convert numpy.ndarray, tuples, etc. to plain Python lists
                    if hasattr(v, "tolist"):
                        cleaned_r[k] = v.tolist()
                    else:
                        cleaned_r[k] = list(v)
                elif pd.isna(v):
                    cleaned_r[k] = None
                else:
                    cleaned_r[k] = v
            cleaned_records.append(cleaned_r)

        # Pydantic v2 uses model_validate to parse dictionaries
        return [model_class.model_validate(r) for r in cleaned_records]

    # CVE
    def save_cves(self, cves: List[CVEModel]) -> None:
        self._save_models(cves, "cve_id", "cve", "cves")

    def load_cves(self) -> List[CVEModel]:
        return self._load_models(CVEModel, "cve", "cves")

    # EPSS
    def save_epss(self, epss: List[EPSSModel]) -> None:
        self._save_models(epss, "cve_id", "epss", "epss")

    def load_epss(self) -> List[EPSSModel]:
        return self._load_models(EPSSModel, "epss", "epss")

    # KEV
    def save_kev(self, kev: List[KEVModel]) -> None:
        self._save_models(kev, "cve_id", "kev", "kev")

    def load_kev(self) -> List[KEVModel]:
        return self._load_models(KEVModel, "kev", "kev")

    # arXiv
    def save_arxiv(self, papers: List[ArXivModel]) -> None:
        self._save_models(papers, "arxiv_id", "arxiv", "arxiv")

    def load_arxiv(self) -> List[ArXivModel]:
        return self._load_models(ArXivModel, "arxiv", "arxiv")

    # GitHub
    def save_github(self, repos: List[GitHubRepoModel]) -> None:
        self._save_models(repos, "repo_id", "github", "repos")

    def load_github(self) -> List[GitHubRepoModel]:
        return self._load_models(GitHubRepoModel, "github", "repos")

    # Notion Sources
    def save_notion_sources(self, sources: List[NotionSourceModel]) -> None:
        self._save_models(sources, "source_id", "notion", "sources")

    def load_notion_sources(self) -> List[NotionSourceModel]:
        return self._load_models(NotionSourceModel, "notion", "sources")

    # Notion Keywords
    def save_notion_keywords(self, keywords: List[AIKeywordModel]) -> None:
        self._save_models(keywords, "keyword", "notion", "keywords")

    def load_notion_keywords(self) -> List[AIKeywordModel]:
        return self._load_models(AIKeywordModel, "notion", "keywords")

    # Notion Products
    def save_notion_products(self, products: List[AIProductModel]) -> None:
        self._save_models(products, "product_name", "notion", "products")

    def load_notion_products(self) -> List[AIProductModel]:
        return self._load_models(AIProductModel, "notion", "products")

    # CWE
    def save_cwe(self, cwes: List[CWEModel]) -> None:
        self._save_models(cwes, "cwe_id", "cwe", "cwes")

    def load_cwe(self) -> List[CWEModel]:
        return self._load_models(CWEModel, "cwe", "cwes")

    # CPE
    def save_cpe(self, cpes: List[CPEModel]) -> None:
        self._save_models(cpes, ["cve_id", "cpe_name"], "cpe", "cpes")

    def load_cpe(self) -> List[CPEModel]:
        return self._load_models(CPEModel, "cpe", "cpes")

    # MITRE ATLAS Tactics
    def save_atlas_tactics(self, tactics: List[ATLASTacticModel]) -> None:
        self._save_models(tactics, "tactic_id", "atlas", "tactics")

    def load_atlas_tactics(self) -> List[ATLASTacticModel]:
        return self._load_models(ATLASTacticModel, "atlas", "tactics")

    # MITRE ATLAS Techniques
    def save_atlas_techniques(self, techniques: List[ATLASTechniqueModel]) -> None:
        self._save_models(techniques, "technique_id", "atlas", "techniques")

    def load_atlas_techniques(self) -> List[ATLASTechniqueModel]:
        return self._load_models(ATLASTechniqueModel, "atlas", "techniques")

    # MITRE ATLAS Case Studies
    def save_atlas_case_studies(self, case_studies: List[ATLASCaseStudyModel]) -> None:
        self._save_models(case_studies, "case_id", "atlas", "case_studies")

    def load_atlas_case_studies(self) -> List[ATLASCaseStudyModel]:
        return self._load_models(ATLASCaseStudyModel, "atlas", "case_studies")

    # GHSA
    def save_ghsa(self, advisories: List[GHSAModel]) -> None:
        self._save_models(advisories, "advisory_id", "ghsa", "advisories")

    def load_ghsa(self) -> List[GHSAModel]:
        return self._load_models(GHSAModel, "ghsa", "advisories")

    # Articles
    def save_articles(self, articles: List[ArticleModel]) -> None:
        self._save_models(articles, "article_id", "rss", "articles")

    def load_articles(self) -> List[ArticleModel]:
        return self._load_models(ArticleModel, "rss", "articles")

    # News
    def save_news(self, news: List[NewsModel]) -> None:
        self._save_models(news, "news_id", "rss", "news")

    def load_news(self) -> List[NewsModel]:
        return self._load_models(NewsModel, "rss", "news")

    # NIST AI RMF
    def save_nist(self, nist_data: List[NISTModel]) -> None:
        self._save_models(nist_data, "control_id", "nist", "nist")

    def load_nist(self) -> List[NISTModel]:
        return self._load_models(NISTModel, "nist", "nist")
