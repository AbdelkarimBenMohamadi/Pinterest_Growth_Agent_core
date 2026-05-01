import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from src.models import Keyword, Pin, Trend, EngagementData

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS keywords (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    term            TEXT NOT NULL,
    suggestion_rank INTEGER,
    related_terms   TEXT,
    source          TEXT DEFAULT 'autosuggest',
    performance_score REAL DEFAULT 0.0,
    discovered_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(term)
);

CREATE TABLE IF NOT EXISTS trends (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    velocity        REAL,
    region          TEXT,
    category        TEXT,
    keywords        TEXT,
    fetched_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pins (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path      TEXT NOT NULL,
    image_hash      TEXT NOT NULL UNIQUE,
    title           TEXT NOT NULL,
    description     TEXT,
    alt_text        TEXT,
    target_keyword  TEXT,
    board_name      TEXT,
    content_type    TEXT,
    status          TEXT DEFAULT 'pending',
    scheduled_at    TIMESTAMP,
    posted_at       TIMESTAMP,
    pinterest_url   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS engagement (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    pin_id          INTEGER REFERENCES pins(id),
    impressions     INTEGER DEFAULT 0,
    saves           INTEGER DEFAULT 0,
    clicks          INTEGER DEFAULT 0,
    ctr             REAL DEFAULT 0.0,
    save_rate       REAL DEFAULT 0.0,
    scraped_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    action          TEXT NOT NULL,
    details         TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS diagnostic_reports (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    scraper_module      TEXT NOT NULL,
    failure_count       INTEGER DEFAULT 0,
    last_error          TEXT,
    diagnosis           TEXT,
    suggested_fix       TEXT,
    status              TEXT DEFAULT 'pending',
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at         TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scraper_health (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    module_name         TEXT NOT NULL,
    run_count           INTEGER DEFAULT 0,
    success_count       INTEGER DEFAULT 0,
    failure_count       INTEGER DEFAULT 0,
    last_run_at         TIMESTAMP,
    last_success_at     TIMESTAMP,
    last_failure_at     TIMESTAMP,
    last_error          TEXT,
    avg_results         REAL DEFAULT 0.0,
    UNIQUE(module_name)
);

CREATE TABLE IF NOT EXISTS selector_cache (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    page_context       TEXT NOT NULL,
    element_desc        TEXT NOT NULL,
    selector           TEXT NOT NULL,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    use_count           INTEGER DEFAULT 0,
    UNIQUE(page_context, element_desc)
);
"""


class Database:
    def __init__(self, db_path: str = "data/pga.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        conn = self._connect()
        try:
            conn.executescript(SCHEMA)
            conn.commit()
            logger.info("Database initialized")
        finally:
            conn.close()

    def upsert_keyword(self, keyword: Keyword) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO keywords (term, suggestion_rank, related_terms, source, performance_score)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(term) DO UPDATE SET
                   suggestion_rank = excluded.suggestion_rank,
                   related_terms = excluded.related_terms,
                   source = excluded.source,
                   performance_score = keywords.performance_score""",
                (
                    keyword.term,
                    keyword.suggestion_rank,
                    json.dumps(keyword.related_terms),
                    keyword.source,
                    keyword.performance_score,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_top_keywords(self, limit: int = 20) -> list[Keyword]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                """SELECT * FROM keywords
                   ORDER BY performance_score DESC, suggestion_rank ASC
                   LIMIT ?""",
                (limit,),
            )
            rows = cursor.fetchall()
            return [self._row_to_keyword(row) for row in rows]
        finally:
            conn.close()

    def update_keyword_score(self, term: str, score: float) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "UPDATE keywords SET performance_score = ? WHERE term = ?",
                (score, term),
            )
            conn.commit()
        finally:
            conn.close()

    def insert_trend(self, trend: Trend) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO trends (name, velocity, region, category, keywords, fetched_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    trend.name,
                    trend.velocity,
                    trend.region,
                    trend.category,
                    json.dumps(trend.keywords),
                    trend.fetched_at.isoformat() if trend.fetched_at else datetime.now(timezone.utc).isoformat(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_recent_trends(self, hours: int = 24) -> list[Trend]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                """SELECT * FROM trends
                   WHERE fetched_at >= datetime('now', ?)
                   ORDER BY velocity DESC""",
                (f"-{hours} hours",),
            )
            rows = cursor.fetchall()
            return [self._row_to_trend(row) for row in rows]
        finally:
            conn.close()

    def insert_pin(self, pin: Pin) -> int:
        conn = self._connect()
        try:
            cursor = conn.execute(
                """INSERT INTO pins (image_path, image_hash, title, description, alt_text,
                   target_keyword, board_name, content_type, status, scheduled_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    pin.image_path,
                    pin.image_hash,
                    pin.title,
                    pin.description,
                    pin.alt_text,
                    pin.target_keyword,
                    pin.board_name,
                    pin.content_type,
                    pin.status,
                    pin.scheduled_at.isoformat() if pin.scheduled_at else None,
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update_pin_status(self, pin_id: int, status: str) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE pins SET status = ? WHERE id = ?", (status, pin_id))
            conn.commit()
        finally:
            conn.close()

    def set_pin_url(self, pin_id: int, url: str) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE pins SET pinterest_url = ? WHERE id = ?", (url, pin_id))
            conn.commit()
        finally:
            conn.close()

    def update_pin_posted(self, pin_id: int, status: str, url: str | None, log_action: str, log_details: dict) -> None:
        """Atomically update pin status + URL + log in a single transaction."""
        conn = self._connect()
        try:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE pins SET status = ?, pinterest_url = ?, posted_at = ? WHERE id = ?",
                (status, url, now if status == "posted" else None, pin_id),
            )
            conn.execute(
                "INSERT INTO agent_log (action, details) VALUES (?, ?)",
                (log_action, json.dumps(log_details)),
            )
            conn.commit()
        finally:
            conn.close()

    def get_pending_pins(self) -> list[Pin]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM pins WHERE status = 'pending' ORDER BY scheduled_at ASC"
            )
            rows = cursor.fetchall()
            return [self._row_to_pin(row) for row in rows]
        finally:
            conn.close()

    def get_recent_pins(self, days: int = 7) -> list[Pin]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                """SELECT * FROM pins
                   WHERE created_at >= datetime('now', ?)
                   ORDER BY created_at DESC""",
                (f"-{days} days",),
            )
            rows = cursor.fetchall()
            return [self._row_to_pin(row) for row in rows]
        finally:
            conn.close()

    def hash_exists(self, image_hash: str) -> bool:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM pins WHERE image_hash = ? LIMIT 1",
                (image_hash,),
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def insert_engagement(self, data: EngagementData) -> None:
        conn = self._connect()
        try:
            conn.execute(
                """INSERT INTO engagement (pin_id, impressions, saves, clicks, ctr, save_rate)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data.pin_id,
                    data.impressions,
                    data.saves,
                    data.clicks,
                    data.ctr,
                    data.save_rate,
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def get_engagement_for_pin(self, pin_id: int) -> list[EngagementData]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM engagement WHERE pin_id = ? ORDER BY scraped_at DESC",
                (pin_id,),
            )
            rows = cursor.fetchall()
            return [self._row_to_engagement(row) for row in rows]
        finally:
            conn.close()

    def log_action(self, action: str, details: dict) -> None:
        conn = self._connect()
        try:
            conn.execute(
                "INSERT INTO agent_log (action, details) VALUES (?, ?)",
                (action, json.dumps(details)),
            )
            conn.commit()
        finally:
            conn.close()

    def _row_to_keyword(self, row: sqlite3.Row) -> Keyword:
        return Keyword(
            term=row["term"],
            suggestion_rank=row["suggestion_rank"] or 0,
            related_terms=json.loads(row["related_terms"]) if row["related_terms"] else [],
            source=row["source"] or "autosuggest",
            performance_score=row["performance_score"] or 0.0,
            discovered_at=datetime.fromisoformat(row["discovered_at"]) if row["discovered_at"] else datetime.now(timezone.utc),
        )

    def _row_to_trend(self, row: sqlite3.Row) -> Trend:
        return Trend(
            name=row["name"],
            velocity=row["velocity"] or 0.0,
            region=row["region"] or "",
            category=row["category"] or "",
            keywords=json.loads(row["keywords"]) if row["keywords"] else [],
            fetched_at=datetime.fromisoformat(row["fetched_at"]) if row["fetched_at"] else datetime.now(timezone.utc),
        )

    def _row_to_pin(self, row: sqlite3.Row) -> Pin:
        return Pin(
            id=row["id"],
            image_path=row["image_path"],
            image_hash=row["image_hash"],
            title=row["title"],
            description=row["description"] or "",
            alt_text=row["alt_text"] or "",
            target_keyword=row["target_keyword"] or "",
            board_name=row["board_name"] or "",
            content_type=row["content_type"] or "seo",
            status=row["status"] or "pending",
            scheduled_at=datetime.fromisoformat(row["scheduled_at"]) if row["scheduled_at"] else None,
            posted_at=datetime.fromisoformat(row["posted_at"]) if row["posted_at"] else None,
            pinterest_url=row["pinterest_url"] or "",
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc),
        )

    def _row_to_engagement(self, row: sqlite3.Row) -> EngagementData:
        return EngagementData(
            pin_id=row["pin_id"],
            impressions=row["impressions"] or 0,
            saves=row["saves"] or 0,
            clicks=row["clicks"] or 0,
            ctr=row["ctr"] or 0.0,
            save_rate=row["save_rate"] or 0.0,
            scraped_at=datetime.fromisoformat(row["scraped_at"]) if row["scraped_at"] else datetime.now(timezone.utc),
        )

    def record_scrape_run(self, module_name: str, success: bool, result_count: int, error: str | None = None) -> None:
        conn = self._connect()
        try:
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("""
                INSERT INTO scraper_health (module_name, run_count, success_count, failure_count, last_run_at, last_success_at, last_failure_at, last_error, avg_results)
                VALUES (?, 1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(module_name) DO UPDATE SET
                    run_count = run_count + 1,
                    success_count = success_count + ?,
                    failure_count = failure_count + ?,
                    last_run_at = ?,
                    last_success_at = CASE WHEN ? THEN ? ELSE last_success_at END,
                    last_failure_at = CASE WHEN NOT ? THEN ? ELSE last_failure_at END,
                    last_error = ?,
                    avg_results = (avg_results * (run_count - 1) + ?) / run_count
            """, (
                module_name,
                1 if success else 0,
                1 if not success else 0,
                now,
                now if success else None,
                now if not success else None,
                error,
                result_count,
                1 if success else 0,
                1 if not success else 0,
                now,
                1 if success else 0,
                now,
                0 if success else 1,
                now if not success else None,
                error,
                result_count,
            ))
            conn.commit()
        finally:
            conn.close()

    def get_scraper_health(self) -> list[dict]:
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT * FROM scraper_health ORDER BY module_name")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def insert_diagnostic_report(self, module_name: str, failure_count: int, last_error: str, diagnosis: str, suggested_fix: str) -> int:
        conn = self._connect()
        try:
            cursor = conn.execute("""
                INSERT INTO diagnostic_reports (scraper_module, failure_count, last_error, diagnosis, suggested_fix, status)
                VALUES (?, ?, ?, ?, ?, 'pending')
            """, (module_name, failure_count, last_error, diagnosis, suggested_fix))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_pending_diagnostics(self) -> list[dict]:
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT * FROM diagnostic_reports WHERE status = 'pending' ORDER BY created_at DESC")
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def resolve_diagnostic(self, report_id: int) -> None:
        conn = self._connect()
        try:
            conn.execute("UPDATE diagnostic_reports SET status = 'resolved', resolved_at = ? WHERE id = ?",
                        (datetime.now(timezone.utc).isoformat(), report_id))
            conn.commit()
        finally:
            conn.close()

    def get_recent_diagnostics(self, limit: int = 10) -> list[dict]:
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT * FROM diagnostic_reports ORDER BY created_at DESC LIMIT ?", (limit,))
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_cached_selector(self, page_context: str, element_desc: str) -> str | None:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT selector FROM selector_cache WHERE page_context = ? AND element_desc = ? LIMIT 1",
                (page_context, element_desc)
            )
            row = cursor.fetchone()
            if row:
                conn.execute(
                    "UPDATE selector_cache SET use_count = use_count + 1 WHERE page_context = ? AND element_desc = ?",
                    (page_context, element_desc)
                )
                conn.commit()
            return row[0] if row else None
        finally:
            conn.close()

    def cache_selector(self, page_context: str, element_desc: str, selector: str) -> None:
        conn = self._connect()
        try:
            conn.execute("""
                INSERT INTO selector_cache (page_context, element_desc, selector)
                VALUES (?, ?, ?)
                ON CONFLICT(page_context, element_desc) DO UPDATE SET
                    selector = excluded.selector,
                    use_count = 0
            """, (page_context, element_desc, selector))
            conn.commit()
        finally:
            conn.close()

    def clear_selector_cache(self) -> None:
        conn = self._connect()
        try:
            conn.execute("DELETE FROM selector_cache")
            conn.commit()
        finally:
            conn.close()