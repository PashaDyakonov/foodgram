from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.safestring import mark_safe

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

    list_display = ('id', 'name', 'slug', 'count_recipes',)
    search_fields = ('name', 'slug',)
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Количество рецептов с этим тэгом')
    def count_recipes(self, tag):
        """Возвращает количество рецептов для тега."""
        return tag.recipes.count()


@admin.register(Ingredients)
class IngredientAdmin(admin.ModelAdmin):
    """Настройка админки для модели Ingredients."""

    list_display = (
        'id',
        'name',
        'measurement_unit',
        'count_recipes',
    )
    search_fields = ('name', 'measurement_unit')
    list_filter = ('measurement_unit',)

    @admin.display(description='Количество рецептов с этим ингредиентом')
    def count_recipes(self, recipe):
        """Количество рецептов, использующих этот ингредиент."""
        return recipe.recipes.count()


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Настройка админки для модели Recipe."""

    list_display = (
        'id',
        'name',
        'cooking_time',
        'get_author_username',
        'favorites_count',
        'ingredients_list',
        'tags_list',
        'image_preview',
    )
    search_fields = ('name', 'tags', 'author')
    list_filter = ('author', 'tags', 'cooking_time')
    readonly_fields = ('image_preview',)

    @admin.display(description='Автор')
    def get_author_username(self, recipe):
        """Возвращает username автора вместо User object."""
        return recipe.author.username

    @admin.display(description='Количество добавлений в избранное')
    def favorites_count(self, recipe):
        """Количество добавлений в избранное."""
        return recipe.favorites.count()

    @admin.display(description='Список ингредиентов')
    @mark_safe
    def ingredients_list(self, recipe):
        return '<br>'.join(
            f'{i.ingredient.name} - {i.amount} {i.ingredient.measurement_unit}'
            for i in recipe.recipe_ingredients.all()
        )

    @admin.display(description='Список тэгов')
    @mark_safe
    def tags_list(self, recipe):
        """Список тегов с HTML-разметкой."""
        return '<br>'.join(tag.name for tag in recipe.tags.all())

    @admin.display(description='Превью')
    @mark_safe
    def image_preview(self, recipe):
        """Превью изображения с HTML-разметкой."""
        if recipe.image:
            return (
                f'<img src="{recipe.image.url}" '
                f'style="max-height: 100px; '
                f'max-width: 100px;" />'
            )
        return 'Нет изображения'


@admin.register(Favorite)
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
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {
            'fields': (
                'avatar',
            )
        }),
    )
    list_display = (
        'pk',
        'username',
        'get_full_name',
        'email',
        'avatar_preview',
        'recipes_count',
        'following_count',
        'followers_count',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    readonly_fields = ('avatar_preview',)

    @admin.display(description='Аватар')
    @mark_safe
    def avatar_preview(self, user):
        """Отображает миниатюру аватара."""
        if user.avatar:
            return (
                f'<img src="{user.avatar.url}" '
                f'style="max-height: 50px; '
                f'max-width: 50px; '
                f'border-radius: 50%;" />'
            )
        return 'Нет изображения'

    @admin.display(description='ФИО')
    def get_full_name(self, user):
        """Возвращает полное имя (ФИО)."""
        if user.first_name or user.last_name:
            return f'{user.first_name} {user.last_name}'
        return 'ФИО отсутствует'

    @admin.display(description='Рецептов')
    def recipes_count(self, user):
        """Количество рецептов пользователя."""
        return user.recipes.count()

    @admin.display(description='Подписок')
    def following_count(self, user):
        """Подписок."""
        return user.followers.count()

    @admin.display(description='Подписчиков')
    def followers_count(self, user):
        """Подписчиков."""
        return user.authors.count()

    @admin.display(description='ID')
    def pk(self, user):
        return user.pk


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Настройка админки для модели Follow."""

    list_display = (
        'id',
        'user',
        'author',
    )
    list_filter = ('user', 'author')
