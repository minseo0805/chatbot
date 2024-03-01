import os
from dotenv import load_dotenv
from .abc_hcx import HyperClovaX
import requests
from ast import literal_eval


class SegmentationExecutor(HyperClovaX):
    """HyperClova 문단 나누기 API 파라미터 설명
    - text (필수): 문단 나누기를 수행할 문서 / - 범위: ~12만자 (한글기준, 공백포함)
    - alpha: 문단 나누기를 위한 thresholds 값. 클수록 나눠지는 문단 수 증가 / - 범위: -1.5 ~ -100 (-100 입력 시 모델이 최적값으로 문단 나누기 자동 수행)
    - segCnt: 원하는 문단 나누기 수 / - 범위: 1이상 (-1로 설정 시 모델이 최적 문단 수로 분리)
    - postProcess: 문단 나누기 수행 후 원하는 길이로 문단을 합치거나 나누는 후처리 수행 여부 / - true: postProcess 관련 파라미터 작동 / - false: postProcess 관련 파라미터 미작동
    - postProcessMaxSize: post process module 적용 시 문단에 포함되는 문자열의 최대 글자 수 / - 범위: 1~3000자 (한글 기준)
    - postProcessMinSize: post process module 적용 시 문단에 포함되는 문자열의 최소 글자 수 / - 범위: 0~segMaxSize
    """

    def __init__(self):
        key_path = "api_keys/.env"
        load_dotenv(dotenv_path=key_path)
        self._api_url = os.getenv("HANG_SEG_URL")
        self._api_key = os.getenv("HANG_API_KEY")
        self._api_key_primary_val = os.getenv("HANG_API_KEY_PRIMARY_VAL")
        self.request_data = dict()

    def set_request_data(self, text: str) -> dict[str]:
        self.request_data = {
            "text": text,
            "alpha": -100,
            "segCnt": -1,
            "postProcess": False,
            "postProcessMaxSize": 500,
            "postProcessMinSize": 300,
        }

    def execute(self) -> list[str]:
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
            result = r.content.decode("utf-8")
            result = literal_eval(result)
            return result["result"]["topicSeg"]
