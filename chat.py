import os
import json
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX


class ChatExecutor(HyperClovaX):
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HCX_URL")
        self._api_key = os.getenv("HCX_API_KEY")
        self._api_key_primary_val = os.getenv("API_KEY_PRIMARY_VAL")

    def set_request_data(
        self, messages: list[dict], additional_system: str = ""
    ) -> None:
        system_input = [{"role": "system", "content": additional_system}]

        self.request_data = {
            "messages": system_input + messages[1:],
            "maxTokens": 256,
            "temperature": 0.5,
            "topK": 0,
            "topP": 0.8,
            "repeatPenalty": 5.0,
            "stopBefore": [],
            "includeAiFilters": True,
        }
        print(self.request_data)

    def execute(self) -> str:
        headers = {
            "X-NCP-CLOVASTUDIO-API-KEY": self._api_key,
            "X-NCP-APIGW-API-KEY": self._api_key_primary_val,
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "text/event-stream",
        }
        with requests.post(
            url=self._api_url,
            headers=headers,
            json=self.request_data,
            stream=True,
            timeout=10,
        ) as r:
            is_result = False
            for line in r.iter_lines():
                content = line.decode("utf-8")
                if is_result:
                    res = json.loads(content[5:])
                    return res.get("message")
                if content == "event:result":
                    is_result = True
