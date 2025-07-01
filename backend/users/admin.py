from django.contrib import admin
from django.contrib.auth import get_user_model

from .models import Follow


User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Настройка админки для модели User."""

    list_display = (
        'pk',
        'username',
        'email',
        'first_name',
        'last_name',
        'avatar'
    )
    search_fields = ('username',)
    list_filter = ('username',)
    empty_value_display = '-пусто-'


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Настройка админки для модели Follow."""

    list_display = (
        'id',
        'user',
        'following',
    )
    list_filter = ('user', 'following')
