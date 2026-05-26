import logging
import os
import sys
import time

import requests

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("wait_for_grobid")

url = os.getenv("GROBID_URL", "http://grobid:8070").rstrip("/") + "/api/isalive"
max_wait = int(os.getenv("GROBID_MAX_WAIT", "600"))

logger.info("Waiting for Grobid at %s (timeout %ds) ...", url, max_wait)
deadline = time.time() + max_wait
while time.time() < deadline:
    try:
        r = requests.get(url, timeout=3)
        if r.text.strip().lower() == "true":
            logger.info("Grobid is ready.")
            sys.exit(0)
    except requests.exceptions.RequestException:
        pass
    logger.info("Grobid not ready yet, retrying in 3s ...")
    time.sleep(3)

logger.error("Grobid did not become ready within %ds.", max_wait)
sys.exit(1)
