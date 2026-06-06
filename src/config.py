import os
from dotenv import load_dotenv

# Load environment variables from .env if it exists
load_dotenv()


class Config:
    # Notion API Settings
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID_SOURCES = os.getenv("NOTION_DATABASE_ID_SOURCES")
    NOTION_DATABASE_ID_KEYWORDS = os.getenv("NOTION_DATABASE_ID_KEYWORDS")
    NOTION_DATABASE_ID_PRODUCTS = os.getenv("NOTION_DATABASE_ID_PRODUCTS")

    # NVD CVE API Settings
    NVD_API_KEY = os.getenv("NVD_API_KEY")
    NVD_API_URL = os.getenv(
        "NVD_API_URL", "https://services.nvd.nist.gov/rest/json/cves/2.0"
    )

    # FIRST EPSS API Settings
    EPSS_API_URL = os.getenv("EPSS_API_URL", "https://api.first.org/data/v1/epss")

    # CISA KEV Feed Settings
    KEV_FEED_URL = os.getenv(
        "KEV_FEED_URL",
        "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
    )

    # arXiv API Settings
    ARXIV_API_URL = os.getenv("ARXIV_API_URL", "https://export.arxiv.org/api/query")

    # HTTP Client Settings
    HTTP_TIMEOUT = int(os.getenv("HTTP_TIMEOUT", "30"))

    @classmethod
    def validate_notion_config(cls):
        """Validate Notion config and raise error if missing."""
        missing = []
        if not cls.NOTION_API_KEY:
            missing.append("NOTION_API_KEY")
        if not cls.NOTION_DATABASE_ID_SOURCES:
            missing.append("NOTION_DATABASE_ID_SOURCES")
        if not cls.NOTION_DATABASE_ID_KEYWORDS:
            missing.append("NOTION_DATABASE_ID_KEYWORDS")
        if not cls.NOTION_DATABASE_ID_PRODUCTS:
            missing.append("NOTION_DATABASE_ID_PRODUCTS")

        if missing:
            raise ValueError(
                f"Missing required Notion configuration: {', '.join(missing)}"
            )
