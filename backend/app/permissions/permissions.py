from app.permissions.roles import Role


def can_delete(role: str) -> bool:
    return role == Role.ADMIN.value


def can_manage(role: str) -> bool:
    return role in [
        Role.ADMIN.value,
        Role.ENGINEER.value,
    ]
