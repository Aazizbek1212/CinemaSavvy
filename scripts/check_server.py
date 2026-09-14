import logging

import requests

logger = logging.getLogger(__name__)

endpoints = [
    "http://127.0.0.1:8000/",
    "http://127.0.0.1:8000/admin/",
    "http://127.0.0.1:8000/movies/",
]


def check_endpoints():
    for url in endpoints:
        try:
            r = requests.get(url, timeout=5)
            logger.info("%s %s", url, r.status_code)
        except Exception as e:
            logger.error("%s ERROR %s", url, e)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    check_endpoints()
