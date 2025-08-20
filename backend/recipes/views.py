from django.shortcuts import redirect
from django.http import Http404

from recipes.models import Recipe


def recipe_shortlink_redirect(self, request, recipe_id):
    """Перенаправление с короткой ссылки на полный рецепт."""
    if not Recipe.objects.filter(id=recipe_id).exists():
        raise Http404(f'Рецепт с ID {recipe_id} не существует')
    return redirect(f'/recipes/{recipe_id}/')
