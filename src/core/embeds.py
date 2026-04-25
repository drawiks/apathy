import discord
from config import EMBED_COLOR


def success_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title.lower(),
        description=description,
        color=EMBED_COLOR
    )


def error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=title.lower(),
        description=description,
        color=0xFF0000
    )


def mod_action_embed(
    action: str,
    member: discord.Member,
    moderator: discord.Member | None = None,
    reason: str | None = None,
    color: int = EMBED_COLOR
) -> discord.Embed:
    description = f"**участник:** {member.mention} ({member.name})\n"
    if moderator:
        description += f"**модератор:** {moderator.mention}\n"
    if reason:
        description += f"**причина:** {reason}"
    
    return discord.Embed(
        title=action.lower(),
        description=description,
        color=color
    )