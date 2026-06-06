from datetime import datetime
from typing import Any, Dict, List, Optional
from src.base_fetcher import BaseFetcher
from src.config import Config
from src.models import AIKeywordModel, AIProductModel, NotionSourceModel

class NotionFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("NotionFetcher")
        # Validate that the Notion config is present
        Config.validate_notion_config()
        self.headers.update({
            "Authorization": f"Bearer {Config.NOTION_API_KEY}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        })

    def _query_database(self, database_id: str) -> List[Dict[str, Any]]:
        """Query a Notion database and return all page results."""
        url = f"https://api.notion.com/v1/databases/{database_id}/query"
        results = []
        has_more = True
        start_cursor = None

        self.logger.info(f"Querying Notion database {database_id}...")
        with self._get_client() as client:
            while has_more:
                payload = {}
                if start_cursor:
                    payload["start_cursor"] = start_cursor
                
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                results.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        self.logger.info(f"Retrieved {len(results)} pages from Notion.")
        return results

    def _get_property_value(self, prop: Dict[str, Any]) -> Any:
        """Extract value from a Notion property based on its type."""
        if not prop:
            return None
        prop_type = prop.get("type")
        
        if prop_type == "title":
            titles = prop.get("title", [])
            return "".join([t.get("plain_text", "") for t in titles]) if titles else ""
        elif prop_type == "rich_text":
            texts = prop.get("rich_text", [])
            return "".join([t.get("plain_text", "") for t in texts]) if texts else ""
        elif prop_type == "number":
            return prop.get("number")
        elif prop_type == "select":
            select = prop.get("select")
            return select.get("name") if select else None
        elif prop_type == "multi_select":
            selections = prop.get("multi_select", [])
            return [s.get("name") for s in selections]
        elif prop_type == "date":
            date_info = prop.get("date")
            return date_info.get("start") if date_info else None
        elif prop_type == "checkbox":
            return prop.get("checkbox", False)
        elif prop_type == "url":
            return prop.get("url")
        elif prop_type == "status":
            status = prop.get("status")
            return status.get("name") if status else None
        elif prop_type == "created_time":
            return prop.get("created_time")
        elif prop_type == "last_edited_time":
            return prop.get("last_edited_time")
        
        return None

    def _get_properties_dict(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Notion page properties dict to a simple key-value dict."""
        properties = page.get("properties", {})
        result = {}
        for prop_name, prop_val in properties.items():
            # Standardize key names (lowercase, space/hyphen/underscore to underscore)
            key = prop_name.lower().replace(" ", "_").replace("-", "_")
            result[key] = self._get_property_value(prop_val)
        return result

    def fetch_sources(self) -> List[NotionSourceModel]:
        """Fetch details from the Notion source database."""
        pages = self._query_database(Config.NOTION_DATABASE_ID_SOURCES)
        results = []
        for page in pages:
            props = self._get_properties_dict(page)
            try:
                # Fallback properties lookup
                created_time = page.get("created_time")
                last_edited_time = page.get("last_edited_time")

                model = NotionSourceModel(
                    source_id=props.get("source_id") or page.get("id"),
                    name=props.get("name") or props.get("title") or "",
                    url=props.get("url") or "",
                    type=props.get("type") or "rss",
                    status=props.get("status") or "active",
                    score=props.get("score"),
                    last_checked_at=props.get("last_checked_at"),
                    created_at=props.get("created_at") or created_time,
                    updated_at=props.get("updated_at") or last_edited_time
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse source page {page.get('id')}: {e}")
        return results

    def fetch_keywords(self) -> List[AIKeywordModel]:
        """Fetch details from the Notion AI keywords database."""
        pages = self._query_database(Config.NOTION_DATABASE_ID_KEYWORDS)
        results = []
        for page in pages:
            props = self._get_properties_dict(page)
            try:
                created_time = page.get("created_time")
                last_edited_time = page.get("last_edited_time")

                model = AIKeywordModel(
                    keyword=props.get("keyword") or props.get("title") or "",
                    category=props.get("category") or "",
                    weight=float(props.get("weight") or 1.0),
                    status=props.get("status") or "active",
                    created_at=props.get("created_at") or created_time,
                    updated_at=props.get("updated_at") or last_edited_time
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse keyword page {page.get('id')}: {e}")
        return results

    def fetch_products(self) -> List[AIProductModel]:
        """Fetch details from the Notion AI products database."""
        pages = self._query_database(Config.NOTION_DATABASE_ID_PRODUCTS)
        results = []
        for page in pages:
            props = self._get_properties_dict(page)
            try:
                model = AIProductModel(
                    product_name=props.get("product_name") or props.get("title") or "",
                    vendor=props.get("vendor") or "",
                    category=props.get("category") or "",
                    aliases=props.get("aliases") or [],
                    weight=float(props.get("weight") or 1.0),
                    status=props.get("status") or "active"
                )
                results.append(model)
            except Exception as e:
                self.logger.warning(f"Failed to parse product page {page.get('id')}: {e}")
        return results

    def fetch(self, **kwargs) -> List[Any]:
        """Fetch all Notion databases and return them as a flat list.
        
        Typically, users should call fetch_sources(), fetch_keywords(), 
        or fetch_products() directly. This method acts as a combined runner.
        """
        self.logger.info("Fetching all Notion databases...")
        sources = self.fetch_sources()
        keywords = self.fetch_keywords()
        products = self.fetch_products()
        return sources + keywords + products
