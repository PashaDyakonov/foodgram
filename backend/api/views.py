from django.contrib.auth import get_user_model
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Ingredients,
    Recipe,
    ShoppingList,
    Tag,
    Follow,
)
from services.shopping_list import generate_shopping_list_content

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
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        content = generate_shopping_list_content(request.user)
        if not content:
            raise ValidationError({'error': 'Список покупок пуст'})

        response = FileResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], url_path='shortlink')
    def generate_short_link(self, request, pk=None):
        """Генерация короткой ссылки."""
        return Response(
            {'short_link': request.build_absolute_uri(
                reverse('recipe-shortlink', kwargs={'pk': pk}))},
            status=status.HTTP_200_OK
        )

    def _manage_related_model(
            self, request, pk, model_class, serializer_class, relation_field):
        """Общий метод для управления избранным и списком покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)

        if request.method == 'DELETE':
            deleted = model_class.objects.filter(
                user=user,
                **{relation_field: recipe}
            ).delete()

            if not deleted[0]:
                return Response(
                    {'error': 'Связь не найдена'},
                    status=status.HTTP_404_NOT_FOUND
                )
            return Response(status=status.HTTP_204_NO_CONTENT)

        _, created = model_class.objects.get_or_create(
            user=user,
            **{relation_field: recipe}
        )

        if not created:
            raise ValidationError(
                {'error': f'Рецепт "{recipe.name}" уже добавлен'},
                code=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            serializer_class(recipe).data,
            status=status.HTTP_201_CREATED
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """Управление избранными рецептами."""
        return self._manage_related_model(
            request,
            pk,
            Favorite,
            ShortRecipeSerializer,
            'recipe'
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='shopping_cart',
        permission_classes=[IsAuthenticated],
    )
    def manage_shopping_cart(self, request, pk=None):
        """Добавление/удаление рецепта из списка покупок."""
        return self._manage_related_model(
            request,
            pk,
            ShoppingList,
            ShortRecipeSerializer,
            'recipe'
        )


class UserViewSet():
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
        return super().me(request)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAuthorOrReadOnly]
    )
    def avatar(self, request):
        """PUT: добавление аватара, DELETE: удаление аватара."""
        user = request.user
        if request.method == 'DELETE':
            user.avatar.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        serializer = AvatarSerializer(
            instance=user,
            data=request.data,
            partial=False,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

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
        serializer = FollowUserSerializer(
            page,
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
    """Управление подпиской на пользователя с валидацией."""
    user = request.user

    if request.method == 'DELETE':
        deleted = user.follower.filter(following_id=pk).delete()
        if deleted[0] == 0:
            return Response(
                {'error': 'Подписка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
    following = get_object_or_404(User, id=pk)

    if user == following:
        return Response(
            {'error': 'Нельзя подписаться на самого себя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    follow, created = Follow.objects.get_or_create(
        user=user,
        following=following,
        defaults={'user': user, 'following': following}
    )
    if not created:
        return Response(
            {'error': 'Вы уже подписаны на этого пользователя'},
            status=status.HTTP_400_BAD_REQUEST
        )
    serializer = FollowUserSerializer(
        follow.following,
        context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_201_CREATED)
