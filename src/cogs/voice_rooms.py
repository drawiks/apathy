from datetime import datetime
import discord
from discord.ext import commands

from config import VOICE_TEMPLATE_CHANNEL, VOICE_CATEGORY, VOICE_CHANNEL_NAME, VOICE_IGNORE_CHANNEL, GUILD, LOG_CHANNEL, EMBED_COLOR
from services import redis_client, stats_repo
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
        cached = redis_client.get_all_channel_owners()
        for channel_id, owner_id in cached.items():
            channel = guild.get_channel(channel_id)
            if channel:
                members = [m for m in channel.members if not m.bot]
                if len(members) == 1 and members[0].id == owner_id:
                    self.temp_channels[channel_id] = owner_id
                elif len(members) > 1:
                    pass
            else:
                redis_client.remove_channel_owner(channel_id)

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
            redis_client.set_channel_owner(new_channel.id, member.id)

            timestamp = datetime.now().timestamp()
            redis_client.set_online(f"voice:{new_channel.id}:{member.id}", timestamp)

            try:
                await member.move_to(new_channel)
            except discord.Forbidden:
                await new_channel.delete()
                return
            except Exception as e:
                await new_channel.delete()
                return

        elif before_channel and before_channel.id in self.temp_channels:
            owner_id = self.temp_channels.get(before_channel.id)
            
            if owner_id == member.id:
                remaining_members = [m for m in before_channel.members if not m.bot]
                if remaining_members:
                    new_owner = remaining_members[0]
                    self.temp_channels[before_channel.id] = new_owner.id
                    redis_client.set_channel_owner(before_channel.id, new_owner.id)
                    timestamp = datetime.now().timestamp()
                    redis_client.set_online(f"voice:{before_channel.id}:{new_owner.id}", timestamp)
                owner_id = self.temp_channels.pop(before_channel.id, None)
                redis_client.remove_channel_owner(before_channel.id)
                join_timestamp = redis_client.get_online(f"voice:{before_channel.id}:{owner_id}")
                
                if join_timestamp:
                    duration_seconds = int(datetime.now().timestamp() - join_timestamp)
                    redis_client.remove_online(f"voice:{before_channel.id}:{owner_id}")

                    stats_repo.add_time(
                        owner_id,
                        guild.id,
                        "voice",
                        duration_seconds
                    )

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