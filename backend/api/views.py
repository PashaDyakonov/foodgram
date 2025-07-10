from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import UserSerializer
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredients, Recipe, ShoppingList, Tag

from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    FollowUserSerializer,
    IngredientsSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    TagSerializer,
)


User = get_user_model()


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientsViewSet(viewsets.ReadOnlyModelViewSet):
    """Вьюсет для ингредиентами ."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    pagination_class = PageNumberPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """Управление избранными рецептами."""
        user = request.user

        if request.method == 'POST':
            favorite, created = Favorite.objects.get_or_create(
                user=user,
                recipe_id=pk
            )

            if not created:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST
                )
            recipe = get_object_or_404(Recipe, id=pk)
            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        deleted, _ = Favorite.objects.filter(
            user=user,
            recipe_id=pk
        ).delete()

        if not deleted:
            return Response(
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        shopping_list = request.user.shoppers.first()
        if not shopping_list:
            return Response(
                {'error': 'Список покупок пуст'},
                status=status.HTTP_404_NOT_FOUND
            )
        recipes = shopping_list.recipe.prefetch_related(
            'recipeingredient_set__ingredient'
        ).all()

        ingredients_dict = {}
        for recipe in recipes:
            for recipe_ingredient in recipe.recipeingredient_set.all():
                ingredient = recipe_ingredient.ingredient
                key = (ingredient.name, ingredient.measurement_unit)
                ingredients_dict[key] = ingredients_dict.get(
                    key, 0) + float(recipe_ingredient.amount)
        text_content = "Список покупок:\n\n"
        for (name, unit), amount in sorted(ingredients_dict.items()):
            text_content += f"{name} - {amount} {unit}\n"

        response = FileResponse(text_content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def generate_short_link(self, request, pk=None):
        """Генерация короткой ссылки."""
        short_url = reverse('recipes:recipe-shortlink', kwargs={'pk': pk})
        absolute_url = request.build_absolute_uri(short_url)
        return Response(
            {'short_link': absolute_url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def manage_shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта из списка покупок."""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        shopping_list, _ = ShoppingList.objects.get_or_create(user=user)

        if request.method == 'POST':
            if shopping_list.recipe.filter(id=recipe.id).exists():
                return Response(
                    {"error": "Рецепт уже в списке покупок!"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_list.recipe.add(recipe)
            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        if not shopping_list.recipe.filter(id=recipe.id).exists():
            return Response(
                {"error": "Рецепта нет в списке покупок"},
                status=status.HTTP_400_BAD_REQUEST
            )
        shopping_list.recipe.remove(recipe)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(UserSerializer):
    """Вьюсет для работы с пользователями и подписками."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']

    @action(
        methods=['get'],
        detail=False,
        url_path='me',
        permission_classes=[IsAuthenticated],
    )
    def get_me(self, request):
        """Получение текущего пользователя."""
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthorOrReadOnly]
    )
    def avatar(self, request):
        """PUT: добавление аватара, DELETE: удаление аватара."""
        user = request.user
        if request.method == "PUT":
            serializer = AvatarSerializer(
                instance=user,
                data=request.data,
                partial=False,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        user.avatar.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='subscriptions',
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение списка подписок с рецептами."""
        following_users = request.user.follower.select_related(
            'following').values_list('following', flat=True)
        queryset = User.objects.filter(
            id__in=following_users).prefetch_related('recipes')
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = FollowUserSerializer(
                page,
                many=True,
                context={'request': request}
            )
            return self.get_paginated_response(serializer.data)

        serializer = FollowUserSerializer(
            queryset,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Управление подпиской на пользователя с валидацией."""
        user = request.user
        following = get_object_or_404(User, id=pk)
        if user == following:
            return Response(
                {"error": "Нельзя подписаться на самого себя"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.method == 'POST':
            if user.follower.filter(following=following).exists():
                return Response(
                    {"error": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow = user.follower.create(following=following)
            serializer = FollowUserSerializer(
                follow.following,
                context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            follow = get_object_or_404(
                user.follower,
                following=following,
                error_message="Подписка не найдена"
            )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    def validate(self, data):
        request = self.context.get('request') 
        user = request.user
        following_id = request.parser_context['kwargs']['pk'] 
        following = get_object_or_404(User, id=following_id) 
        if user == following:
            raise serializers.ValidationError(
                {"error": "Подписка самого на себя запрещена."}
            )
        if user.follower.filter(following=following).exists():
            raise serializers.ValidationError(
                {"error": "Вы уже подписаны на этого автора."}
            )
        data['following'] = following
        return data

    def to_representation(self, instance):
        return FollowUserSerializer(instance, context=self.context).data
