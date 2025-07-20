from django.shortcuts import redirect
from django.http import Http404
from recipes.models import Recipe


def recipe_shortlink_redirect(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт."""
    if not Recipe.objects.filter(pk=pk).exists():
        raise Http404

    return redirect(f'/recipes/{pk}/')
