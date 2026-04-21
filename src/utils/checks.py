from config import MODERATOR_ROLES


def is_moderator(user):
    if user.guild_permissions.administrator:
        return True
    for role in user.roles:
        if role.id in MODERATOR_ROLES:
            return True
    return False