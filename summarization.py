import os
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX
from ast import literal_eval


class SummarizationExecutor(HyperClovaX):
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("SUMMARY_URL")
        self._api_key = os.getenv("API_KEY")
        self._api_key_primary_val = os.getenv("API_KEY_PRIMARY_VAL")

    def set_request_data(self, texts: list[str]):
        self.request_data = {
            "texts": texts,
            "segMinSize": 300,
            "includeAiFilters": True,
            "maxTokens": 256,
            "autoSentenceSplitter": True,
            "segCount": -1,
            "segMaxSize": 1000,
        }

    def execute(self) -> str:
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self._api_key,
            "X-NCP-APIGW-API-KEY": self._api_key_primary_val,
            "Content-Type": "application/json; charset=utf-8",
        }
        with requests.post(
            url=self._api_url,
            headers=headers,
            json=self.request_data,
            stream=False,
            timeout=10,
        ) as r:
            # result = r.json().get("result").get("text")
            # return r.text
            result = r.content.decode("utf-8")
            result = literal_eval(result)
            return result
