from abc import ABC, abstractmethod
import logging
from typing import Any, List
import httpx
from src.config import Config

# Setup base logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class BaseFetcher(ABC):
    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(name)
        # Setup headers
        self.headers = {
            "User-Agent": "Security-for-AI-Monitor/1.0.0"
        }

    def _get_client(self) -> httpx.Client:
        """Create and return an HTTP client with default settings."""
        return httpx.Client(
            headers=self.headers,
            timeout=Config.HTTP_TIMEOUT,
            follow_redirects=True
        )

    @abstractmethod
    def fetch(self, **kwargs) -> List[Any]:
        """Fetch data from the source and return parsed models.
        
        Raises:
            Exception: If fetching or parsing fails.
        """
        pass
