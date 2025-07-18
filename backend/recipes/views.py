from django.shortcuts import redirect, get_object_or_404
from recipes.models import Recipe


def recipe_shortlink_redirect(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт."""
    return redirect(f'/recipes/{pk}/')
