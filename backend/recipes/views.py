from django.shortcuts import redirect


def recipe_shortlink_redirect(request, pk): 
    """Перенаправление с короткой ссылки на полный рецепт."""
    return redirect(f'/recipes/{pk}/')
