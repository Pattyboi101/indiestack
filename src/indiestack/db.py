"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import re
import math
import json
import time
import random
import string
import hashlib
import unicodedata
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.environ.get("DB_PATH", "indiestack.db")