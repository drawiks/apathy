from dataclasses import dataclass
from datetime import datetime
from tinydb import TinyDB, Query


@dataclass
class GameStats:
    user_id: int
    guild_id: int
    game: str
    total_seconds: int
    last_updated: int


class StatsRepository:
    def __init__(self, filename: str = "game_stats.json") -> None:
        self.db = TinyDB(filename)
        self.table = self.db.table("stats")

    def add_time(
        self, user_id: int, guild_id: int, game: str, seconds: int
    ) -> None:
        if seconds <= 0:
            return
        current = self.get_total(user_id, guild_id, game)
        new_total = current + seconds
        now = int(datetime.now().timestamp())
        
        Stats = Query()
        existing = self.table.search(
            (Stats.user_id == user_id) 
            & (Stats.guild_id == guild_id) 
            & (Stats.game == game)
        )
        
        if existing:
            self.table.update(
                {"total_seconds": new_total, "last_updated": now},
                (Stats.user_id == user_id) 
                & (Stats.guild_id == guild_id) 
                & (Stats.game == game)
            )
        else:
            self.table.insert({
                "user_id": user_id,
                "guild_id": guild_id,
                "game": game,
                "total_seconds": new_total,
                "last_updated": now
            })

    def get_total(self, user_id: int, guild_id: int, game: str) -> int:
        Stats = Query()
        result = self.table.search(
            (Stats.user_id == user_id) 
            & (Stats.guild_id == guild_id) 
            & (Stats.game == game)
        )
        if result:
            return result[0]["total_seconds"]
        return 0

    def get_leaderboard(
        self, guild_id: int, game: str, limit: int = 5
    ) -> list[GameStats]:
        Stats = Query()
        results = self.table.search(
            (Stats.guild_id == guild_id) & (Stats.game == game)
        )
        sorted_results = sorted(
            results, 
            key=lambda x: x["total_seconds"], 
            reverse=True
        )[:limit]
        return [
            GameStats(
                user_id=r["user_id"],
                guild_id=r["guild_id"],
                game=r["game"],
                total_seconds=r["total_seconds"],
                last_updated=r["last_updated"]
            )
            for r in sorted_results
        ]


stats_repo = StatsRepository()