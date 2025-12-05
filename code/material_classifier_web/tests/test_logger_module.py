import os
import sys
import logging

# make project modules importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger import get_logger
from config import Config


def test_get_logger_has_handlers():
    lg = get_logger()
    assert isinstance(lg, logging.Logger)
    # has at least two handlers (file + console)
    assert len(lg.handlers) >= 2
    # level matches config
    assert lg.level == Config.LOG_LEVEL
