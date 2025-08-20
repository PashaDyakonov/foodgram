from django_filters.rest_framework import (
    BooleanFilter,
    FilterSet,
    ModelMultipleChoiceFilter
)
from rest_framework.filters import SearchFilter

from recipes.models import Recipe, Tag


class IngredientFilter(SearchFilter):
    """Фильтрация по ингридиентам."""

    search_param = 'name'


class RecipeFilter(FilterSet):
    """Фильтраци для рецептов."""

    tags = ModelMultipleChoiceFilter(
        queryset=Tag.objects.all(),
        field_name='tags__slug',
        to_field_name='slug',
    )
    is_favorited = BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = BooleanFilter(
        method='filter_shopping_cart'
    )

    class Meta:
        model = Recipe
        fields = ('tags', 'author', 'is_favorited', 'is_in_shopping_cart')

    def filter_favorited(self, recipes, name, value):
        user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )
        if value and user:
            return recipes.filter(favorites__user_id=user.id)
        return recipes

    def filter_shopping_cart(self, recipes, name, value):
        user = (
            self.request.user
            if self.request.user.is_authenticated
            else None
        )
        if value and user:
            return recipes.filter(shopping_carts__user_id=user.id)
        return recipes
