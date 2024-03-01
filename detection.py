# 네이버 Papago 언어감지 API 예제
import os
import requests
from dotenv import load_dotenv

class LangDetect():
    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HANG_DET_URL")
        self._api_id = os.getenv("HANG_PAPAGO_API_KEY_ID")
        self._api_key = os.getenv("HANG_PAPAGO_API_KEY")

    def set_request_data(self, text: str):
        self.request_data = {"query": text}
                
    def execute(self) -> list[float]:
        headers = {
            "X-NCP-APIGW-API-KEY-ID": "x716pa3nrb",
            "X-NCP-APIGW-API-KEY":"VIC3HsUEwcpvRMtBJQlIHe8eoTjQDYRutwo7nn77",
            "Content-Type": "application/json; charset=utf-8",
        }
        with requests.post(
            url="https://naveropenapi.apigw.ntruss.com/langs/v1/dect",
            headers=headers,
            json=self.request_data,
            stream=True,
        ) as r:
            result = r.json()
            return result["langCode"]