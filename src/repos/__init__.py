from .redis import RedisRepo
from .tinydb import ApathyRepo

redis_voice = RedisRepo("voice")
redis_dota = RedisRepo("dota")

warning = ApathyRepo("warnings")
role_message = ApathyRepo("role_messages")
stats = ApathyRepo("stats")

__all__ = [
    "redis_voice",
    "redis_dota",
    "warning",
    "role_message",
    "stats",
    "RedisRepo",
    "ApathyRepo",
]