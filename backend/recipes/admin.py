from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .apps import count_recipes
from users.models import Follow
from .models import Ingredients, Recipe, RecipeIngredient, Tag


User = get_user_model()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели RecipeIngredient."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админки для модели Tag."""

    list_display = ('id', 'name', 'slug', count_recipes,)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели Ingredients."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit')


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админки для модели Recipe."""

    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        'tags',
    )
    search_fields = ('name', 'tags',)
    list_filter = ('author', 'tags', 'cooking_time')


@admin.register(Follow)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админки для модели Favorite."""

    list_display = (
        'id',
        'user',
        'recipe',
    )
    list_filter = ('user', 'recipe')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Настройка админки для модели User."""

    list_display = (
        'pk',
        'username',
        'email',
        'avatar',
        'is_active',
        count_recipes,
    )
    search_fields = ('username',)
    list_filter = ('username', 'email',)
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
