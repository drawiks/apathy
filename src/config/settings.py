from environs import Env

env = Env()
env.read_env()

BOT_TOKEN: str = env("BOT_TOKEN")

REDIS_HOST: str = "localhost"
REDIS_PORT: int = 6379

EMBED_COLOR: int = 0xffe26c

AUTO_MOD_ENABLED: bool = True
SPAM_LIMIT: int = 5
SPAM_TIMEOUT_SECONDS: int = 300