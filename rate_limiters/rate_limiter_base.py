from abc import ABC, abstractmethod


class RateLimiterBase(ABC):
    @abstractmethod
    def allow_request(self, key: str):
        pass
