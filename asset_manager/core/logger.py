"""Module defining logging functionality for the application"""

import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Literal


LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)


# HTTP Request Logger
http_logger = logging.getLogger("http_logger")
for handler in http_logger.handlers[:]:
    http_logger.removeHandler(handler)
http_handler = RotatingFileHandler(
    f"{LOG_DIR}/http_requests.log", maxBytes=1000000, backupCount=3
)
http_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
http_logger.setLevel(logging.INFO)
http_logger.addHandler(http_handler)


# Database Logger
db_modify_logger = logging.getLogger("db_modify_logger")
for handler in db_modify_logger.handlers[:]:
    db_modify_logger.removeHandler(handler)
db_modify_handler = RotatingFileHandler(
    f"{LOG_DIR}/db_changes.log", maxBytes=1000000, backupCount=3
)
db_modify_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
db_modify_logger.setLevel(logging.INFO)
db_modify_logger.addHandler(db_modify_handler)

# Database Logger
db_access_logger = logging.getLogger("db_access_logger")
for handler in db_access_logger.handlers[:]:
    db_access_logger.removeHandler(handler)
db_access_handler = RotatingFileHandler(
    f"{LOG_DIR}/db_access.log", maxBytes=1000000, backupCount=3
)
db_access_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))
db_access_logger.setLevel(logging.INFO)
db_access_logger.addHandler(db_access_handler)


def log_db_usage(
    action: Literal["select", "insert", "update", "delete"],
    table: str,
    user: str,
    details: str,
):
    """Log changes to the db in a standard format"""
    if action == "select":
        logger = db_access_logger
    else:
        logger = db_modify_logger
    logger.info("%s on %s by %s: %s", action.upper(), table, user, details)
