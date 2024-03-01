import os
import json
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX
#from my_prompts import *


class ChatExecutor(HyperClovaX):
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HCX_URL")
        self._api_key = os.getenv("HANG_HCX_API_KEY_A")
        self._api_key_primary_val = os.getenv("HANG_API_KEY_PRIMARY_VAL")
        self.request_data = dict()
        
    def set_api_key(self, api_key: str):
         self._api_key = api_key
         
    def set_request_data(
        self,
        max_tokens: int,
        temperature: float,
        top_k: int,
        top_p: float,
        repeat_penalty: float,
        messages: list[dict],
        system_message: str = "",
    ) -> None:
        system_input = [{"role": "system", "content": system_message}]
        self.request_data = {
            "messages": system_input + messages,  # 인사말 제외
            "maxTokens": max_tokens,
            "temperature": temperature,
            "topK": top_k,
            "topP": top_p,
            "repeatPenalty": repeat_penalty,
            "stopBefore": [],
            "includeAiFilters": True,
        }

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
            is_error = False
            for line in r.iter_lines():
                content = line.decode("utf-8")

                if is_result:
                    res = json.loads(content[5:])
                    return res.get("message")
                if is_error:
                    res = json.loads(content[5:])
                    error_message = res.get("status")
                    return error_message

                if content == "event:result":
                    is_result = True
                if content == "event:error":
                    is_error = True
