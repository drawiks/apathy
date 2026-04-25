from discord import Member, User
from config import MODERATOR_ROLES, IMMUNE_ROLES


def is_moderator(user: Member | User) -> bool:
    if not hasattr(user, 'guild') or user.guild is None:
        return False
    if user.guild_permissions.administrator:
        return True
    for role in user.roles:
        if role.id in MODERATOR_ROLES:
            return True
    return False


def is_immune(user: Member | User) -> bool:
    if not hasattr(user, 'guild') or user.guild is None:
        return False
    for role in user.roles:
        if role.id in IMMUNE_ROLES:
            return True
    return False