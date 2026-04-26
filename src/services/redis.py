import redis
from config import REDIS_HOST, REDIS_PORT


class RedisClient:
    def __init__(self) -> None:
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def set_online(self, key: str, timestamp: float) -> None:
        self.client.set(f"{key}", timestamp)

    def get_online(self, key: str) -> float | None:
        value = self.client.get(f"{key}")
        return float(value) if value else None

    def remove_online(self, key: str) -> None:
        self.client.delete(f"{key}")

    def get_all(self, pattern: str) -> list[tuple[str, float]]:
        keys = self.client.keys(pattern)
        result = []
        for key in keys:
            timestamp = self.client.get(key)
            result.append((key, float(timestamp)))
        return result

    def get_all_online(self) -> list[tuple[int, float]]:
        keys = self.client.keys("dota:online:*")
        result = []
        for key in keys:
            user_id = int(key.split(":")[-1])
            timestamp = float(self.client.get(key))
            result.append((user_id, timestamp))
        return result

    def add_play_time(self, user_id: int, seconds: int) -> None:
        self.client.incrby(f"dota:total:{user_id}", seconds)
        self.client.incrby(f"dota:weekly:{user_id}", seconds)

    def get_total_time(self, user_id: int) -> int:
        value = self.client.get(f"dota:total:{user_id}")
        return int(value) if value else 0

    def get_weekly_time(self, user_id: int) -> int:
        value = self.client.get(f"dota:weekly:{user_id}")
        return int(value) if value else 0

    def get_weekly_leaderboard(self, limit: int = 5) -> list[tuple[int, int]]:
        keys = self.client.keys("dota:weekly:*")
        result = []
        for key in keys:
            user_id = int(key.split(":")[-1])
            seconds = int(self.client.get(key) or 0)
            result.append((user_id, seconds))
        result.sort(key=lambda x: x[1], reverse=True)
        return result[:limit]

    def reset_weekly(self) -> None:
        keys = self.client.keys("dota:weekly:*")
        if keys:
            self.client.delete(*keys)

    def set_channel_owner(self, channel_id: int, owner_id: int) -> None:
        self.client.hset("voice:channels", channel_id, owner_id)

    def get_channel_owner(self, channel_id: int) -> int | None:
        value = self.client.hget("voice:channels", channel_id)
        return int(value) if value else None

    def remove_channel_owner(self, channel_id: int) -> None:
        self.client.hdel("voice:channels", channel_id)

    def get_all_channel_owners(self) -> dict[int, int]:
        data = self.client.hgetall("voice:channels")
        return {int(k): int(v) for k, v in data.items()}


redis_client = RedisClient()