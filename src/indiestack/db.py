"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import hashlib
import secrets
import re
from typing import Optional
from datetime import datetime, timedelta, timezone
import time as _time