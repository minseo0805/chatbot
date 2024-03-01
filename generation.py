import os
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX


class GenerationExecutor(HyperClovaX):
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HCX_URL")
        self._api_key = os.getenv("HCX_API_KEY")
        self._api_key_primary_val = os.getenv("API_KEY_PRIMARY_VAL")

    def set_request_data(self, system_input: str, user_input: str):
        preset_text = [
            {"role": "system", "content": system_input},
            {"role": "user", "content": user_input},
        ]
        self.request_data = {
            "messages": preset_text,
            "maxTokens": 1024,
            "temperature": 0.5,
            "topK": 0,
            "topP": 0.8,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
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
            stream=True,
            timeout=10,
        ) as r:
            return r.json().get("result").get("message").get("content")
