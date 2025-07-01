from django.core.exceptions import ValidationError

from users.constants import FORBIDDEN_NAMES


def validate_username(username):
    if username.lower() in FORBIDDEN_NAMES:
        raise ValidationError(
            f'Зарезервированный логин {username}, нельзя использолвать'
        )
    return username
