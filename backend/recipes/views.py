from django.shortcuts import redirect
from django.http import Http404
from recipes.models import Recipe


def short_link_redirect(request, recipe_id):
    """Функция для редиректа по короткой ссылке."""

    if not Recipe.objects.filter(short_id=recipe_id).exists():
        raise Http404("Рецепт не найден")
    return redirect(f'/recipes/{recipe_id}/')
