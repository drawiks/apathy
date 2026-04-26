import redis
from config import REDIS_HOST, REDIS_PORT


class RedisRepo:
    def __init__(self, prefix: str):
        self._prefix = prefix
        self._client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def _key(self, *parts: str) -> str:
        return f"{self._prefix}:{':'.join(parts)}"

    def set(self, key: str, value) -> None:
        self._client.set(self._key(key), value)

    def get(self, key: str) -> str | None:
        return self._client.get(self._key(key))

    def delete(self, key: str) -> None:
        self._client.delete(self._key(key))

    def get_all(self, pattern: str = "*") -> list[str]:
        keys = self._client.keys(self._key(pattern))
        return [self._client.get(k) for k in keys if self._client.get(k)]