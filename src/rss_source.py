import hashlib
from datetime import datetime, timezone
import email.utils
from typing import Any, List, Tuple, Optional
import xmltodict
from src.base_fetcher import BaseFetcher
from src.models import ArticleModel, NewsModel, NotionSourceModel


class RSSFetcher(BaseFetcher):
    def __init__(self):
        super().__init__("RSSFetcher")

    def _parse_rss_date(self, date_str: Optional[str]) -> datetime:
        """Parse RSS/Atom date string into timezone-aware datetime."""
        if not date_str:
            return datetime.now(timezone.utc)
        try:
            # Try parsing RFC 822 (standard RSS date format)
            return email.utils.parsedate_to_datetime(date_str)
        except Exception:
            try:
                # Try ISO 8601 (Atom date format)
                # Remove Z or replace it with offset
                clean_str = date_str.replace("Z", "+00:00")
                return datetime.fromisoformat(clean_str)
            except Exception:
                # Fallback to current UTC time
                return datetime.now(timezone.utc)

    def _extract_link(self, link_field: Any) -> str:
        """Robustly extract href from RSS/Atom link field."""
        if not link_field:
            return ""
        if isinstance(link_field, str):
            return link_field.strip()
        if isinstance(link_field, dict):
            return link_field.get("@href", link_field.get("#text", "")).strip()
        if isinstance(link_field, list):
            for item in link_field:
                extracted = self._extract_link(item)
                if extracted:
                    return extracted
        return ""

    def _generate_id(self, prefix: str, url: str) -> str:
        """Generate a unique ID based on MD5 hash of URL."""
        hashed = hashlib.md5(url.encode("utf-8")).hexdigest()
        return f"{prefix}_{hashed[:16]}"

    def fetch_feed(
        self, source: NotionSourceModel
    ) -> Tuple[List[ArticleModel], List[NewsModel]]:
        """Fetch a single RSS feed and return parsed Article and News models."""
        self.logger.info(f"Fetching RSS feed from: {source.name} ({source.url})")

        articles = []
        news_list = []

        try:
            with self._get_client() as client:
                response = client.get(source.url, timeout=15.0)
                response.raise_for_status()
                xml_content = response.text
        except Exception as e:
            self.logger.error(f"Failed to fetch RSS feed {source.name}: {e}")
            return [], []

        try:
            feed_dict = xmltodict.parse(xml_content)
        except Exception as e:
            self.logger.error(f"Failed to parse XML content for {source.name}: {e}")
            return [], []

        # Find items / entries
        items = []
        channel = (
            feed_dict.get("rss", {}).get("channel", {})
            if isinstance(feed_dict.get("rss"), dict)
            else {}
        )
        if channel:
            raw_items = channel.get("item", [])
            items = raw_items if isinstance(raw_items, list) else [raw_items]
        else:
            # Try Atom feed structure
            feed = feed_dict.get("feed", {})
            if isinstance(feed, dict):
                raw_entries = feed.get("entry", [])
                items = raw_entries if isinstance(raw_entries, list) else [raw_entries]

        self.logger.info(f"Found {len(items)} items in feed {source.name}.")

        for item in items:
            if not isinstance(item, dict):
                continue

            title = item.get("title", "")
            if isinstance(title, dict):
                title = title.get("#text", "")
            title = str(title).strip()

            url = self._extract_link(item.get("link"))
            if not url:
                continue

            # Parse publication date
            pub_date_raw = (
                item.get("pubDate") or item.get("published") or item.get("updated")
            )
            published_at = self._parse_rss_date(pub_date_raw)
            fetched_at = datetime.now(timezone.utc)

            # Extract summary
            summary = (
                item.get("description") or item.get("summary") or item.get("content")
            )
            if isinstance(summary, dict):
                summary = summary.get("#text", "")
            if summary:
                # Strip HTML tags simply if present
                import re

                summary = re.sub("<[^<]+?>", "", str(summary)).strip()
                # Truncate if too long
                summary = summary[:300] + "..." if len(summary) > 300 else summary
            else:
                summary = None

            # Determine whether to save as News or Article
            if source.type.lower() in ["news", "news_media"]:
                news_id = self._generate_id("news", url)
                news_model = NewsModel(
                    news_id=news_id,
                    title=title,
                    url=url,
                    source=source.name,
                    published_at=published_at,
                    summary=summary,
                    mentioned_cve=[],
                    mentioned_products=[],
                    mentioned_threat_actors=[],
                    category=None,
                    importance_score=0.0,
                )
                news_list.append(news_model)
            else:
                article_id = self._generate_id("art", url)
                article_model = ArticleModel(
                    article_id=article_id,
                    title=title,
                    url=url,
                    source_name=source.name,
                    source_type=source.type,
                    published_at=published_at,
                    fetched_at=fetched_at,
                    summary=summary,
                    category=None,
                    owasp_mapping=[],
                    mitre_mapping=[],
                    nist_mapping=[],
                    importance_score=0.0,
                )
                articles.append(article_model)

        return articles, news_list

    def fetch(
        self, sources: List[NotionSourceModel], **kwargs
    ) -> Tuple[List[ArticleModel], List[NewsModel]]:
        """Fetch RSS feeds from a list of active RSS sources.

        Args:
            sources: List of NotionSourceModel instances representing sources.

        Returns:
            Tuple of (List[ArticleModel], List[NewsModel])
        """
        all_articles = []
        all_news = []

        # Filter active RSS feeds
        active_rss_sources = [
            src
            for src in sources
            if src.status.lower() == "active"
            and src.type.lower()
            in ["rss", "vendor_blog", "news", "news_media", "official", "research_blog"]
        ]

        self.logger.info(
            f"Starting crawl for {len(active_rss_sources)} active RSS sources..."
        )

        for source in active_rss_sources:
            articles, news = self.fetch_feed(source)
            all_articles.extend(articles)
            all_news.extend(news)

        self.logger.info(
            f"RSS fetch complete. Total Articles: {len(all_articles)}, Total News: {len(all_news)}"
        )
        return all_articles, all_news
