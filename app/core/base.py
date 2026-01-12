from abc import ABC, abstractmethod


class RateLimiterStrategy(ABC):
    @abstractmethod
    async def is_request_allowed(self, key: str) -> bool:
        pass
