from datetime import datetime
import discord
from discord.ext import commands

from config import VOICE_TEMPLATE_CHANNEL, VOICE_CATEGORY, VOICE_CHANNEL_NAME, VOICE_IGNORE_CHANNEL, GUILD, LOG_CHANNEL, EMBED_COLOR
from repos import redis_voice, stats
from utils.formatters import format_duration


class VoiceRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {}

    async def cog_load(self):
        guild = self.bot.get_guild(GUILD)
        if guild:
            await self._sync_channels(guild)

    async def _sync_channels(self, guild):
        all_keys = redis_voice.get_all("owner:*")
        for key in all_keys:
            try:
                channel_id = int(key.split(":")[-1])
                channel = guild.get_channel(channel_id)
                if channel:
                    members = [m for m in channel.members if not m.bot]
                    if members:
                        self.temp_channels[channel_id] = int(redis_voice.get(key))
                else:
                    redis_voice.delete(f"owner:{channel_id}")
            except (ValueError, IndexError):
                continue

    async def cog_unload(self):
        self.temp_channels.clear()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return

        guild = member.guild
        template_channel = guild.get_channel(VOICE_TEMPLATE_CHANNEL)
        category = guild.get_channel(VOICE_CATEGORY)

        before_channel = before.channel
        after_channel = after.channel

        if after_channel and after_channel.id == VOICE_IGNORE_CHANNEL:
            return
        if before_channel and before_channel.id == VOICE_IGNORE_CHANNEL:
            return

        if after_channel and after_channel.id == VOICE_TEMPLATE_CHANNEL:
            channel_name = VOICE_CHANNEL_NAME.replace("{user}", member.display_name)

            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                user_limit=0
            )

            self.temp_channels[new_channel.id] = member.id
            redis_voice.set(f"owner:{new_channel.id}", member.id)
            redis_voice.set(f"online:{new_channel.id}:{member.id}", datetime.now().timestamp())

            try:
                await member.move_to(new_channel)
            except discord.Forbidden:
                await new_channel.delete()
                return
            except Exception:
                await new_channel.delete()
                return

        elif before_channel and before_channel.id in self.temp_channels:
            owner_id = self.temp_channels.get(before_channel.id)

            if owner_id == member.id:
                remaining_members = [m for m in before_channel.members if not m.bot]
                if remaining_members:
                    new_owner = remaining_members[0]
                    self.temp_channels[before_channel.id] = new_owner.id
                    redis_voice.set(f"owner:{before_channel.id}", new_owner.id)
                    redis_voice.set(f"online:{before_channel.id}:{new_owner.id}", datetime.now().timestamp())

                owner_id = self.temp_channels.pop(before_channel.id, None)
                redis_voice.delete(f"owner:{before_channel.id}")
                join_timestamp = redis_voice.get(f"online:{before_channel.id}:{owner_id}")

                if join_timestamp:
                    duration_seconds = int(datetime.now().timestamp() - float(join_timestamp))
                    redis_voice.delete(f"online:{before_channel.id}:{owner_id}")

                    existing = stats.find_one(user_id=owner_id, guild_id=guild.id, game="voice")
                    if existing:
                        existing["total_seconds"] = existing.get("total_seconds", 0) + duration_seconds
                        existing["weekly_seconds"] = existing.get("weekly_seconds", 0) + duration_seconds
                        stats.update(existing, existing.get("doc_id"))
                    else:
                        stats.insert({
                            "user_id": owner_id,
                            "guild_id": guild.id,
                            "game": "voice",
                            "total_seconds": duration_seconds,
                            "weekly_seconds": duration_seconds
                        })

                    session_time = format_duration(duration_seconds)
                    member_color = member.colour if member.colour != discord.Colour.default() else EMBED_COLOR
                    embed = discord.Embed(
                        title=f"{member.display_name} ({member.name}) вышел из голосового",
                        description=f"общался: {session_time}",
                        color=member_color
                    )
                    embed.set_thumbnail(url=member.display_avatar.url)
                    try:
                        log_channel = guild.get_channel(LOG_CHANNEL)
                        await log_channel.send(embed=embed)
                    except:
                        pass

                try:
                    await before_channel.delete()
                except Exception:
                    pass


async def setup(bot):
    await bot.add_cog(VoiceRooms(bot))