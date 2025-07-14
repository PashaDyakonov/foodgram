from django.shortcuts import redirect
from django.urls import reverse
from rest_framework.decorators import api_view


@api_view(['GET'])
def recipe_shortlink_redirect(request, pk):
    """Перенаправление с короткой ссылки на полный рецепт."""
    return redirect(reverse('recipes-detail', kwargs={'pk': pk}))