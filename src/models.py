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


class CWEModel(BaseModel):
    cwe_id: str
    name: str
    description: str
    abstraction: str
    status: str


class CPEModel(BaseModel):
    cve_id: str
    cpe_name: str
    vulnerable: bool
    vendor: str
    product: str
    version_start: Optional[str] = None
    version_end: Optional[str] = None
    version_start_including: Optional[str] = None
    version_end_including: Optional[str] = None


class ATLASTacticModel(BaseModel):
    tactic_id: str
    name: str
    description: str


class ATLASTechniqueModel(BaseModel):
    technique_id: str
    tactic_id: str
    name: str
    description: str
    mitigations: List[str] = Field(default_factory=list)
    examples: List[str] = Field(default_factory=list)

    @field_validator("mitigations", "examples", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class ATLASCaseStudyModel(BaseModel):
    case_id: str
    title: str
    summary: str
    related_techniques: List[str] = Field(default_factory=list)
    url: str

    @field_validator("related_techniques", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class GHSAModel(BaseModel):
    advisory_id: str
    ghsa_id: str
    cve_id: Optional[str] = None
    summary: str
    severity: str
    affected_package: str
    patched_versions: Optional[str] = None
    published_at: datetime
    updated_at: datetime
    url: str


class ArticleModel(BaseModel):
    article_id: str
    title: str
    url: str
    source_name: str
    source_type: str
    published_at: datetime
    fetched_at: datetime
    summary: Optional[str] = None
    category: Optional[str] = None
    owasp_mapping: List[str] = Field(default_factory=list)
    mitre_mapping: List[str] = Field(default_factory=list)
    nist_mapping: List[str] = Field(default_factory=list)
    importance_score: Optional[float] = None

    @field_validator("owasp_mapping", "mitre_mapping", "nist_mapping", mode="before")
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)


class NewsModel(BaseModel):
    news_id: str
    title: str
    url: str
    source: str
    published_at: datetime
    summary: Optional[str] = None
    mentioned_cve: List[str] = Field(default_factory=list)
    mentioned_products: List[str] = Field(default_factory=list)
    mentioned_threat_actors: List[str] = Field(
        default_factory=list, alias="mentioned_threat_actots"
    )
    category: Optional[str] = None
    importance_score: Optional[float] = None

    @field_validator(
        "mentioned_cve", "mentioned_products", "mentioned_threat_actors", mode="before"
    )
    @classmethod
    def validate_lists(cls, v: Any) -> List[str]:
        return parse_list_field(v)

    class Config:
        populate_by_name = True
