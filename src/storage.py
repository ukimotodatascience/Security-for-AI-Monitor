import os
import pandas as pd
from typing import List, TypeVar, Type
from pydantic import BaseModel
from src.models import (
    CVEModel,
    EPSSModel,
    KEVModel,
    ArXivModel,
    GitHubRepoModel,
    NotionSourceModel,
    AIKeywordModel,
    AIProductModel,
)

T = TypeVar("T", bound=BaseModel)


class FileStorage:
    """Storage class to handle saving and loading Pydantic models to/from Parquet files.

    Performs Upsert operations using defined primary keys to avoid duplicate entries.
    """

    def __init__(self, base_dir: str = "data/raw"):
        self.base_dir = base_dir

    def _save_models(
        self, items: List[T], primary_key: str, folder: str, filename: str
    ) -> None:
        """Saves a list of Pydantic models to a Parquet file, executing an Upsert

        based on the primary key.
        """
        if not items:
            return

        # Ensure directory exists
        target_dir = os.path.join(self.base_dir, folder)
        os.makedirs(target_dir, exist_ok=True)
        filepath = os.path.join(target_dir, f"{filename}.parquet")

        # Convert Pydantic models to dictionaries
        # Using model_dump() keeps date/datetime objects, which pandas translates well for Parquet.
        data = [item.model_dump() for item in items]
        new_df = pd.DataFrame(data)

        # Check if existing file exists to merge
        if os.path.exists(filepath):
            try:
                existing_df = pd.read_parquet(filepath)
                # Concatenate existing and new data
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            except Exception:
                # If read fails, fallback to using new data only
                combined_df = new_df
        else:
            combined_df = new_df

        # Remove duplicates based on the primary key, keeping the last (newest) record
        combined_df.drop_duplicates(subset=[primary_key], keep="last", inplace=True)

        # Write back to Parquet
        combined_df.to_parquet(filepath, index=False)

    def _load_models(self, model_class: Type[T], folder: str, filename: str) -> List[T]:
        """Loads a list of Pydantic models from a Parquet file."""
        filepath = os.path.join(self.base_dir, folder, f"{filename}.parquet")
        if not os.path.exists(filepath):
            return []

        df = pd.read_parquet(filepath)
        records = df.to_dict(orient="records")

        # Pydantic v2 uses model_validate to parse dictionaries
        return [model_class.model_validate(r) for r in records]

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
