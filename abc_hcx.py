from abc import ABCMeta, abstractclassmethod

class HyperClovaX(metaclass=ABCMeta):
    def __init__(self, host, api_key, api_key_primary_val, request_id):
        self._host = host
        self._api_key = api_key
        self._api_key_primary_val = api_key_primary_val

    @abstractclassmethod
    def execute(self):
        pass
