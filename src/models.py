from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class Keyword:
    term: str
    suggestion_rank: int = 0
    related_terms: list[str] = field(default_factory=list)
    source: str = "autosuggest"
    performance_score: float = 0.0
    discovered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class Trend:
    name: str
    velocity: float = 0.0
    region: str = ""
    category: str = ""
    keywords: list[str] = field(default_factory=list)
    fetched_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ContentBrief:
    target_keyword: str
    content_type: str
    priority: int = 1
    related_terms: list[str] = field(default_factory=list)
    board_name: str = ""


@dataclass
class PinMetadata:
    title: str
    description: str
    alt_text: str
    suggested_board: str = ""
    hashtags: list[str] = field(default_factory=list)
    destination_link_mode: str = "none"
    default_destination_link: str = ""


@dataclass
class Pin:
    id: int = 0
    image_path: str = ""
    image_hash: str = ""
    title: str = ""
    description: str = ""
    alt_text: str = ""
    target_keyword: str = ""
    board_name: str = ""
    content_type: str = "seo"
    status: str = "pending"
    scheduled_at: datetime | None = None
    posted_at: datetime | None = None
    pinterest_url: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EngagementData:
    pin_id: int = 0
    impressions: int = 0
    saves: int = 0
    clicks: int = 0
    ctr: float = 0.0
    save_rate: float = 0.0
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DailyLimits:
    max_pins: int = 1
    max_actions: int = 10