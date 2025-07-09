from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.serializers import UserSerializer
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import Favorite, Ingredients, Recipe, ShoppingList, Tag
from .filters import IngredientFilter, RecipeFilter
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer,
    DownloadShoppingCartSerializer,
    FollowSerializer,
    IngredientsSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    ShoppingCartSerializer,
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
        permission_classes=[IsAuthorOrReadOnly],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(
                user=self.request.user,
                recipe=recipe
            ).exists():
                return Response(
                    {'error': 'Рецепт уже в избранном'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=self.request.user, recipe=recipe)
            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )

        favorite = get_object_or_404(
            Favorite,
            user=self.request.user,
            recipe=recipe,
            error_message='Рецепта нет в избранном'
        )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        """Скачивание списка покупок."""
        shopping_list = get_object_or_404(ShoppingList, user=request.user)
        serializer = DownloadShoppingCartSerializer(shopping_list)
        text_content = "Список покупок:\n\n"
        setting_response = 'attachment; filename="shopping_list.txt"'
        for ingredient in serializer.data['ingredients']:
            text_content += (
                f"{ingredient['name']} — "
                f"{ingredient['amount']} {ingredient['measurement_unit']}\n"
            )
        response = FileResponse(text_content, content_type='text/plain')
        response['Content-Disposition'] = setting_response
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
    def manage_recipe(self, request, pk=None):
        """POST: Добавление в список покупок, DELETE: убрать из списка."""
        serializer = ShoppingCartSerializer(
            data={},
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        shopping_list = validated_data['shopping_list']
        recipe = validated_data['recipe']
        if request.method == 'POST':
            shopping_list.recipe.add(recipe)
            return Response(
                ShortRecipeSerializer(recipe).data,
                status=status.HTTP_201_CREATED
            )
        elif request.method == 'DELETE':
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
        serializer_class=UserSerializer,
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        """Получение всех подписок."""
        pages = self.paginate_queryset(request.user.follower.all())
        serializer = FollowSerializer(
            pages,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        """Управление подпиской на пользователя."""
        user = request.user
        following = get_object_or_404(User, id=pk)

        if request.method == 'POST':
            if user.follower.filter(following=following).exists():
                return Response(
                    {"error": "Вы уже подписаны на этого пользователя"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            follow = user.follower.create(following=following)
            return Response(
                FollowSerializer(
                    follow, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        get_object_or_404(user.follower, following=following).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
