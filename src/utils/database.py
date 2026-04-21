from datetime import datetime
from tinydb import TinyDB, Query

db = TinyDB("database.json")
warnings = db.table("warnings")


def add_warning(user_id: int, guild_id: int, reason: str, moderator_id: int):
    warnings.insert({
        "user_id": user_id,
        "guild_id": guild_id,
        "reason": reason,
        "moderator_id": moderator_id,
        "timestamp": int(datetime.now().timestamp())
    })


def get_warnings(user_id: int, guild_id: int):
    User = Query()
    return warnings.search((User.user_id == user_id) & (User.guild_id == guild_id))


def remove_warnings(user_id: int, guild_id: int):
    User = Query()
    warnings.remove((User.user_id == user_id) & (User.guild_id == guild_id))