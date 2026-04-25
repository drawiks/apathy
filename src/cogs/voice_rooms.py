import discord
from discord.ext import commands

from config import VOICE_TEMPLATE_CHANNEL, VOICE_CATEGORY, VOICE_CHANNEL_NAME


class VoiceRooms(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.temp_channels = {}

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

        if after_channel and after_channel.id == VOICE_TEMPLATE_CHANNEL:
            channel_name = VOICE_CHANNEL_NAME.replace("{user}", member.display_name)

            new_channel = await guild.create_voice_channel(
                name=channel_name,
                category=category,
                user_limit=0
            )

            self.temp_channels[new_channel.id] = member.id

            try:
                await member.move_to(new_channel)
            except discord.Forbidden:
                await new_channel.delete()
                return
            except Exception as e:
                await new_channel.delete()
                return

        elif before_channel and before_channel.id in self.temp_channels:
            if not before_channel.members:
                owner_id = self.temp_channels.pop(before_channel.id, None)
                try:
                    await before_channel.delete()
                except Exception:
                    pass


async def setup(bot):
    await bot.add_cog(VoiceRooms(bot))