import redis
from config import REDIS_HOST, REDIS_PORT


class RedisClient:
    def __init__(self) -> None:
        self.client = redis.Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            decode_responses=True
        )

    def set_online(self, user_id: int, timestamp: float) -> None:
        self.client.set(f"dota:online:{user_id}", timestamp)

    def get_online(self, user_id: int) -> float | None:
        value = self.client.get(f"dota:online:{user_id}")
        return float(value) if value else None

    def remove_online(self, user_id: int) -> None:
        self.client.delete(f"dota:online:{user_id}")

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


redis_client = RedisClient()