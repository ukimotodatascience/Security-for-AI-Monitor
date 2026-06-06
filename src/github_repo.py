import os
from typing import List, Optional
from src.base_fetcher import BaseFetcher
from src.models import GitHubRepoModel


class GitHubRepoFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("GitHubRepoFetcher")
        # Read GitHub Token if present
        self.token = os.getenv("GITHUB_TOKEN")
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        # Specify GitHub API media type
        self.headers["Accept"] = "application/vnd.github.v3+json"

    def fetch_repo_details(self, repo_name: str) -> Optional[GitHubRepoModel]:
        """Fetch details for a specific repository (e.g. 'protectai/modelscan')."""
        url = f"https://api.github.com/repos/{repo_name}"
        self.logger.info(
            f"Fetching details for repository '{repo_name}' from GitHub API..."
        )

        try:
            with self._get_client() as client:
                response = client.get(url)
                response.raise_for_status()
                data = response.json()

            return self._map_to_model(data)
        except Exception as e:
            self.logger.error(f"Failed to fetch details for {repo_name}: {e}")
            return None

    def search_repositories(self, query: str, limit: int = 10) -> List[GitHubRepoModel]:
        """Search repositories using GitHub Search API (e.g. 'topic:ml-security')."""
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "per_page": min(limit, 100)}
        self.logger.info(
            f"Searching repositories with query '{query}' from GitHub API..."
        )

        try:
            with self._get_client() as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

            items = data.get("items", [])
            results = []
            for item in items:
                model = self._map_to_model(item)
                if model:
                    results.append(model)
            return results
        except Exception as e:
            self.logger.error(
                f"Failed to search repositories with query '{query}': {e}"
            )
            return []

    def _map_to_model(self, item: dict) -> GitHubRepoModel:
        """Helper to map GitHub API response dictionary to GitHubRepoModel."""
        # Convert API fields to schema requirements
        return GitHubRepoModel(
            repo_id=str(item.get("id")),
            full_name=item.get("full_name", ""),
            description=item.get("description"),
            html_url=item.get("html_url", ""),
            stars=item.get("stargazers_count", 0),
            forks=item.get("forks_count", 0),
            language=item.get("language"),
            topics=item.get("topics", []),
            created_at=item.get("created_at"),
            updated_at=item.get("updated_at"),
            pushed_at=item.get("pushed_at"),
            matched_keywords=[],  # Handled by downstream matching logic
            category=None,
        )

    def fetch(
        self, repo_names: List[str] = None, search_query: str = None, **kwargs
    ) -> List[GitHubRepoModel]:
        """Fetch repositories details.

        Args:
            repo_names: List of 'owner/repo' strings to fetch directly.
            search_query: Search query string to search for repositories.
        """
        results = []
        if repo_names:
            for name in repo_names:
                model = self.fetch_repo_details(name)
                if model:
                    results.append(model)

        if search_query:
            limit = kwargs.get("limit", 10)
            search_results = self.search_repositories(search_query, limit=limit)
            results.extend(search_results)

        # Deduplicate results by repo_id
        seen = set()
        deduped = []
        for r in results:
            if r.repo_id not in seen:
                seen.add(r.repo_id)
                deduped.append(r)

        return deduped
