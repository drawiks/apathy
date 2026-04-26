from dataclasses import dataclass
from datetime import datetime
from tinydb import TinyDB, Query


@dataclass
class Warning:
    user_id: int
    guild_id: int
    reason: str
    moderator_id: int
    timestamp: int


@dataclass
class RoleMessage:
    guild_id: int
    message_id: int
    emoji: str
    role_id: int


class WarningRepository:
    def __init__(self) -> None:
        self.db = TinyDB("database.json")
        self.table = self.db.table("warnings")
    
    def add(
        self, 
        user_id: int, 
        guild_id: int, 
        reason: str, 
        moderator_id: int
    ) -> Warning:
        warning = Warning(
            user_id=user_id,
            guild_id=guild_id,
            reason=reason,
            moderator_id=moderator_id,
            timestamp=int(datetime.now().timestamp())
        )
        
        self.table.insert({
            "user_id": warning.user_id,
            "guild_id": warning.guild_id,
            "reason": warning.reason,
            "moderator_id": warning.moderator_id,
            "timestamp": warning.timestamp
        })
        
        return warning
    
    def get(self, user_id: int, guild_id: int) -> list[Warning]:
        User = Query()
        results = self.table.search(
            (User.user_id == user_id) & (User.guild_id == guild_id)
        )
        
        return [
            Warning(
                user_id=r["user_id"],
                guild_id=r["guild_id"],
                reason=r["reason"],
                moderator_id=r["moderator_id"],
                timestamp=r["timestamp"]
            )
            for r in results
        ]
    
    def remove(self, user_id: int, guild_id: int) -> int:
        User = Query()
        return self.table.remove(
            (User.user_id == user_id) & (User.guild_id == guild_id)
        )


class RoleMessageRepository:
    def __init__(self) -> None:
        self.db = TinyDB("database.json")
        self.table = self.db.table("role_messages")

    def add(self, guild_id: int, message_id: int, emoji: str, role_id: int) -> None:
        self.table.insert({
            "guild_id": guild_id,
            "message_id": message_id,
            "emoji": emoji,
            "role_id": role_id
        })

    def get_by_message(self, message_id: int) -> list[RoleMessage]:
        Msg = Query()
        results = self.table.search(Msg.message_id == message_id)
        return [
            RoleMessage(
                guild_id=r["guild_id"],
                message_id=r["message_id"],
                emoji=r["emoji"],
                role_id=r["role_id"]
            )
            for r in results
        ]

    def get_by_guild(self, guild_id: int) -> list[RoleMessage]:
        Guild = Query()
        results = self.table.search(Guild.guild_id == guild_id)
        return [
            RoleMessage(
                guild_id=r["guild_id"],
                message_id=r["message_id"],
                emoji=r["emoji"],
                role_id=r["role_id"]
            )
            for r in results
        ]

    def remove_by_message(self, message_id: int) -> int:
        Msg = Query()
        return self.table.remove(Msg.message_id == message_id)


role_message_repo = RoleMessageRepository()


def add_warning(
    user_id: int, 
    guild_id: int, 
    reason: str, 
    moderator_id: int
) -> None:
    warning_repo.add(user_id, guild_id, reason, moderator_id)


def get_warnings(user_id: int, guild_id: int) -> list[dict]:
    warnings = warning_repo.get(user_id, guild_id)
    return [
        {
            "user_id": w.user_id,
            "guild_id": w.guild_id,
            "reason": w.reason,
            "moderator_id": w.moderator_id,
            "timestamp": w.timestamp
        }
        for w in warnings
    ]


def remove_warnings(user_id: int, guild_id: int) -> None:
    warning_repo.remove(user_id, guild_id)