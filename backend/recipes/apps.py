from django.apps import AppConfig


class RecipesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'recipes'
    verbose_name = 'Рецепты'


def count_recipes(tag):
    """Возвращает количество рецептов для тега."""
    return tag.recipes.count()
