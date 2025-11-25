import requests
from typing import Dict, Any
from config import settings
from utils.logger import setup_logger

logger = setup_logger(__name__)


class PowerAPIService:
    BASE_URL = 'https://be-svitlo.oe.if.ua/schedule-by-search'
    HEADERS = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://svitlo.oe.if.ua",
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/142.0.0.0 Safari/537.36",
        "Referer": "https://svitlo.oe.if.ua/"
    }

    @classmethod
    def get_queue_schedule(cls) -> Dict[str, Any]:
        """
        get schedule data from power company API
        """
        data = {
            "accountNumber": settings.ACCOUNT_NUMBER,
            "userSearchChoice": "pob",
            "address": "",
        }

        try:
            response = requests.post(cls.BASE_URL, headers=cls.HEADERS, data=data, timeout=30)

            if 'application/json' in response.headers.get('Content-Type', ''):
                return response.json()
        except Exception as e:
            logger.error(f"ERROR: API Request Failed: {e}")
            return {}

        return {}
