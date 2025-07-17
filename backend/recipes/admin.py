from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe
from django.utils.html import format_html

from .models import (
    Follow,
    Favorite,
    Ingredients,
    Recipe,
    RecipeIngredient,
    Tag,
)


User = get_user_model()


@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели RecipeIngredient."""

    list_display = ('id', 'recipe', 'ingredient', 'amount')
    search_fields = ('recipe',)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Настройка админки для модели Tag."""

    list_display = ('id', 'name', 'slug',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}

    def count_recipes(tag):
        """Возвращает количество рецептов для тега."""
        return tag.recipes.count()


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели Ingredients."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
        TagAdmin.count_recipes,
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админки для модели Recipe."""

    list_display = (
        'id',
        'name',
        'cooking_time',
        'author',
        TagAdmin.count_recipes,
        'favorites_count',
        'ingredients_list',
        'tags_list',
        'image_preview',
    )
    search_fields = ('name', 'tags', 'author')
    list_filter = ('author', 'tags', 'cooking_time')
    readonly_fields = ('image_preview',)

    def favorites_count(self, recipe):
        """Количество добавлений в избранное."""
        return recipe.favorites.count()

    @mark_safe
    def ingredients_list(self, obj):
        """Список ингредиентов с HTML-разметкой."""
        return (f'{ing.ingredient.name} - {ing.amount} '
                f'{ing.ingredient.measurement_unit}'
                for ing in obj.recipe_ingredients.all()
                )

    @mark_safe
    def tags_list(self, obj):
        """Список тегов с HTML-разметкой."""
        return [tag.name for tag in obj.tags.all()]

    @mark_safe
    def image_preview(self, preview):
        """Превью изображения с HTML-разметкой."""
        if preview.image:
            return format_html(
                '<img src="{}"'
                'style="max-height: 100px;'
                'max-width: 100px;" />',
                preview.image.url
            )
        return "Нет изображения"


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    """Настройка админки для модели Favorite."""

    list_display = (
        'id',
        'user',
        'recipe',
        TagAdmin.count_recipes,
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
        TagAdmin.count_recipes,
        RecipeAdmin.favorites_count,
        RecipeAdmin.ingredients_list,
        RecipeAdmin.tags_list,
        RecipeAdmin.image_preview,
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
        'author',
    )
    list_filter = ('user', 'author')
