import os
import json
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX


class CountingExecutor(HyperClovaX):
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HANG_COUNT_URL")
        self._api_key = os.getenv("HANG_API_KEY")
        self._api_key_primary_val = os.getenv("HANG_API_KEY_PRIMARY_VAL")

    # def set_request_data(self, texts: list[str]) -> None:
    #     self.request_data = {'messages': [{"role" : "user", "content" : text} for text in texts]}

    def set_request_data(self, datas: list[dict]) -> None:
        self.request_data = {"messages": datas}

    def execute(self) -> list[dict]:
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self._api_key,
            "X-NCP-APIGW-API-KEY": self._api_key_primary_val,
            "Content-Type": "application/json; charset=utf-8",
        }

        with requests.post(
            url=self._api_url,
            headers=headers,
            json=self.request_data,
            stream=True,
            timeout=10,
        ) as r:
            result = r.json().get("result").get("messages")
            return result
