import logging
import sys

from app.config import ENVIRONMENT


def setup_logging() -> logging.Logger:
    logger = logging.getLogger("travel_agent")
    if logger.handlers:
        return logger  # already configured (avoid duplicate handlers on reload)

    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)

    if ENVIRONMENT == "production":
        # Plain key=value style plays nicer with log aggregators (Datadog, CloudWatch, etc)
        fmt = "%(asctime)s level=%(levelname)s logger=%(name)s msg=%(message)s"
    else:
        fmt = "%(asctime)s [%(levelname)s] %(message)s"

    handler.setFormatter(logging.Formatter(fmt))
    logger.addHandler(handler)
    return logger


logger = setup_logging()
