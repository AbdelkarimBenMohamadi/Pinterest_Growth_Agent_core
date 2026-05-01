import pytest
import sys
from pathlib import Path
import os
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.store.database import Database
from src.models import Keyword, Pin, Trend, EngagementData


def test_database_initialize():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        conn = db._connect()
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        assert "keywords" in tables
        assert "pins" in tables
        assert "trends" in tables
        assert "engagement" in tables
        assert "agent_log" in tables
    finally:
        os.unlink(db_path)


def test_keyword_roundtrip():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        kw = Keyword(term="test keyword", suggestion_rank=1, related_terms=["a", "b"])
        db.upsert_keyword(kw)
        results = db.get_top_keywords(limit=10)
        assert len(results) >= 1
        assert results[0].term == "test keyword"
        assert results[0].related_terms == ["a", "b"]
    finally:
        os.unlink(db_path)


def test_update_keyword_score():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        kw = Keyword(term="score test", suggestion_rank=5)
        db.upsert_keyword(kw)
        db.update_keyword_score("score test", 2.5)
        results = db.get_top_keywords(limit=10)
        updated = next((k for k in results if k.term == "score test"), None)
        assert updated is not None
        assert updated.performance_score == 2.5
    finally:
        os.unlink(db_path)


def test_pin_insert_and_status():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        pin = Pin(
            image_path="/assets/test.png",
            image_hash="abc123",
            title="Test Pin",
            description="Test desc",
            target_keyword="test kw",
        )
        pin_id = db.insert_pin(pin)
        assert pin_id > 0
        db.update_pin_status(pin_id, "posted")
        pending = db.get_pending_pins()
        assert all(p.status != "posted" for p in pending)
    finally:
        os.unlink(db_path)


def test_hash_exists():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        pin = Pin(image_path="/assets/unique.png", image_hash="uniquehash123", title="U", description="D", target_keyword="t")
        db.insert_pin(pin)
        assert db.hash_exists("uniquehash123") is True
        assert db.hash_exists("nonexistent") is False
    finally:
        os.unlink(db_path)


def test_log_action():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        db = Database(db_path)
        db.initialize()
        db.log_action("test_action", {"key": "value"})
        conn = db._connect()
        cursor = conn.execute("SELECT action, details FROM agent_log")
        row = cursor.fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "test_action"
        assert "value" in row[1]
    finally:
        os.unlink(db_path)