#!/usr/bin/env python3
# Config constants

from __future__ import unicode_literals
from pathlib import Path

from loguru import logger as log

DB_NAME = "whisperx.sqlite"
LOG_TABLE = "logs"
JOB_TABLE = "jobs"
JOB_STATES = ['NEW', 'RUNNING', 'DONE']

# We need absolute path for DB otherwise os.cwd breaks this
DB_PATH = str(Path(DB_NAME))
