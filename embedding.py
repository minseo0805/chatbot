import os
import requests
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX


class EmbeddingExecutor(HyperClovaX):
    """HyperClova 임베딩 API 파라미터 설명
    - text (필수): 임베딩 수행 텍스트 / - 범위: ~500(토큰)
    """

    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HANG_EMBED_URL")
        self._api_key = os.getenv("HANG_API_KEY")
        self._api_key_primary_val = os.getenv("HANG_API_KEY_PRIMARY_VAL")

    def set_request_data(self, text: str):
        self.request_data = {"text": text}

    def execute(self) -> list[float]:
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
            try:
                result = r.json()["result"]["embedding"]
            except Exception as e:
                print(e)
                result = "error"
            return result
