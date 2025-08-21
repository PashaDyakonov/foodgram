from django.contrib.auth import get_user_model
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from recipes.models import (
    Favorite,
    Follow,
    Ingredients,
    Recipe,
    ShoppingList,
    Tag,
)
from api.services.shopping_list import generate_shopping_list_content
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

    def get_serializer_context(self):
        """Добавляем request в контекст сериализатора."""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @action(
        detail=False,
        methods=['get'],
        url_path='download_shopping_cart',
        permission_classes=[IsAuthenticated]
    )
    def download_shopping_cart(self, request):
        content = generate_shopping_list_content(request.user)
        response = FileResponse(content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def get_link(self, request, pk=None):
        exists = Recipe.objects.filter(id=pk).exists()
        if not exists:
            raise Http404(f'Рецепт с id={pk} не найден')
        short_path = reverse(
            'recipes:recipe-short-link', kwargs={'recipe_id': pk})
        absolute_url = request.build_absolute_uri(short_path)

        return Response({'short-link': absolute_url})

    def _manage_related_model(
            self, request, pk, model_class):
        """Общий метод для управления избранным и списком покупок."""
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        if model_class == Favorite:
            serializer_class = ShortRecipeSerializer
            relation_field = 'recipe'
            model_name = 'избранное'
        elif model_class == ShoppingList:
            serializer_class = ShortRecipeSerializer
            relation_field = 'recipe'
            model_name = 'список покупок'
        if request.method == 'DELETE':
            relation = get_object_or_404(
                model_class,
                user=user,
                **{relation_field: recipe}
            )
            relation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        _, created = model_class.objects.get_or_create(
            user=user,
            **{relation_field: recipe}
        )

        if not created:
            raise ValidationError(
                {'error': f'Рецепт "{recipe.name}" уже есть в {model_name}'},
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
        )


class UserViewSet(DjoserUserViewSet):
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
        return self.get_paginated_response(
            FollowUserSerializer(
                self.paginate_queryset(
                    User.objects.filter(
                        id__in=request.user.followers.select_related(
                            'following').values_list(
                                'following',
                                flat=True)).prefetch_related(
                                    'recipes')
                ),
                many=True,
                context={'request': request}).data
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        url_path='subscribe',
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, id=None):
        """Управление подпиской на пользователя с валидацией."""
        user = request.user
        author_id = id

        if request.method == 'DELETE':
            get_object_or_404(
                Follow,
                user=user,
                author_id=author_id).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        author = get_object_or_404(User, id=author_id)

        if user == author:
            return Response(
                {'error': 'Нельзя подписаться на самого себя'},
                status=status.HTTP_400_BAD_REQUEST
            )

        _, created = Follow.objects.get_or_create(
            user=user,
            author=author,
            defaults={'user': user, 'author': author}
        )

        if not created:
            return Response(
                {'error': f'Вы уже подписаны на {author.username}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = FollowUserSerializer(
            author,
            context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
