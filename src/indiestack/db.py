"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import hashlib
import secrets
import re
from typing import Optional
from datetime import datetime, timedelta, timezone
import time as _time

DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
_UPVOTE_SALT = os.environ.get("INDIESTACK_UPVOTE_SALT", "indiestack-default-salt-change-me")

_SEARCH_STOP_WORDS = {"tool", "tools", "for", "best", "top", "the", "a", "an", "and", "or", "with", "in", "to"}

def normalize_search_query(query: str) -> str:
    """Normalize a search query for grouping: lowercase, strip punctuation, remove stop words."""
    q = query.lower().strip()
    q = re.sub(r'[^a-z0-9\s]', ' ', q)
    q = re.sub(r'\s+', ' ', q).strip()
    words = [w for w in q.split() if w not in _SEARCH_STOP_WORDS]
    return " ".join(words) if words else q