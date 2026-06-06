from datetime import date, datetime
import json
from typing import Any, List, Optional
from pydantic import BaseModel, Field, field_validator


def parse_list_field(v: Any) -> List[str]:
    """Helper to parse Union[str, List[str]] into List[str]"""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(item) for item in v]
    if isinstance(v, str):
        v = v.strip()
        if not v:
            return []
        if v.startswith("[") and v.endswith("]"):
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except Exception:
                pass
        return [item.strip() for item in v.split(",") if item.strip()]
    return [str(v)]


class CVEModel(BaseModel):
    cve_id: str
    published_at: datetime
    last_modified_at: datetime
    description: str
    cvss_version: Optional[str] = None
    cvss_base_score: Optional[float] = None
    cvss_base_label: Optional[str] = None
    cwe_ids: List[str] = Field(default_factory=list)
    cpe_names: List[str] = Field(default_factory=list)

    @field_validator("cwe_ids", "cpe_names", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class EPSSModel(BaseModel):
    cve_id: str
    epss: float
    percentile: float
    date: date


class KEVModel(BaseModel):
    cve_id: str
    product: str
    # Keep spelling identical to sheet definition 'vulnerablity_name'
    vulnerablity_name: str = Field(alias="vulnerability_name")
    added_date: date
    due_date: date
    known_ransomware_campaign_use: str
    required_action: str
    notes: Optional[str] = None

    class Config:
        populate_by_name = True


class ArXivModel(BaseModel):
    arxiv_id: str
    title: str
    authors: List[str] = Field(default_factory=list)
    summary: str
    published_at: datetime
    updated_at: datetime
    categories: List[str] = Field(default_factory=list)
    pdf_url: str
    abs_url: str
    keywords_matched: List[str] = Field(default_factory=list)
    owasp_mapping: List[str] = Field(default_factory=list)
    mitre_mapping: List[str] = Field(default_factory=list)
    importance_score: Optional[float] = None

    @field_validator(
        "authors",
        "categories",
        "keywords_matched",
        "owasp_mapping",
        "mitre_mapping",
        mode="before",
    )
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class GitHubRepoModel(BaseModel):
    repo_id: str
    full_name: str
    description: Optional[str] = None
    html_url: str
    stars: int
    forks: int
    language: Optional[str] = None
    topics: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    pushed_at: Optional[str] = None
    matched_keywords: List[str] = Field(default_factory=list)
    category: Optional[str] = None

    @field_validator("topics", "matched_keywords", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class NotionSourceModel(BaseModel):
    source_id: str
    name: str
    url: str
    type: str
    status: str
    score: Optional[int] = None
    last_checked_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class AIKeywordModel(BaseModel):
    keyword: str
    category: str
    weight: float
    status: str
    created_at: datetime
    updated_at: datetime


class AIProductModel(BaseModel):
    product_name: str
    vendor: str
    category: str
    aliases: List[str] = Field(default_factory=list)
    weight: float
    status: str

    @field_validator("aliases", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)
