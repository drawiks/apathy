import discord
from discord.ext import commands

from config import EMBED_COLOR

role_messages = {}


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        if payload.guild_id not in role_messages:
            return

        message_id = payload.message_id
        if message_id not in role_messages[payload.guild_id]:
            return

        emoji = str(payload.emoji)
        role_id = role_messages[payload.guild_id].get(message_id, {}).get(emoji)
        if role_id is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        role = guild.get_role(role_id)
        if role:
            try:
                await member.add_roles(role)
            except discord.Forbidden:
                pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.guild_id is None:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if guild is None:
            return

        if payload.guild_id not in role_messages:
            return

        message_id = payload.message_id
        if message_id not in role_messages[payload.guild_id]:
            return

        emoji = str(payload.emoji)
        role_id = role_messages[payload.guild_id].get(message_id, {}).get(emoji)
        if role_id is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            return

        role = guild.get_role(role_id)
        if role:
            try:
                await member.remove_roles(role)
            except discord.Forbidden:
                pass


async def setup(bot):
    await bot.add_cog(Moderation(bot))
