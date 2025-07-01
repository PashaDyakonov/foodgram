from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .filters import IngredientFilter, RecipeFilter
from .persmissions import IsAdminAuthorOrReadOnly
from recipes.models import Favorite, Ingredients, Recipe, ShoppingList, Tag
from .serializers import (
    AvatarSerializer,
    DownloadShoppingCartSerializer,
    FavoriteSerializer,
    FollowDetailSerializer,
    FollowSerializer,
    IngredientsSerializer,
    PasswordChangeSerializer,
    RecipeReadSerializer,
    RecipeWriteSerializer,
    ShortRecipeSerializer,
    ShortLinkSerializer,
    ShoppingCartSerializer,
    TagSerializer,
    UserSerializer,
    UserRegistrationSerializer,
)


User = get_user_model()


class TagViewSet(viewsets.ModelViewSet):
    """Вьюсет для тегов."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None
    http_method_names = ['get']


class IngredientsViewSet(viewsets.ModelViewSet):
    """Вьюсет для ингредиентами ."""

    queryset = Ingredients.objects.all()
    serializer_class = IngredientsSerializer
    pagination_class = None
    http_method_names = ['get']
    filter_backends = (IngredientFilter,)
    search_fields = ('^name',)


class RecipeViewSet(viewsets.ModelViewSet):
    """Вьюсет для рецептов."""

    queryset = Recipe.objects.all()
    http_method_names = ['get', 'post', 'patch', 'delete']
    permission_classes = [IsAdminAuthorOrReadOnly]
    filter_backends = (DjangoFilterBackend,)
    pagination_class = PageNumberPagination
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return RecipeReadSerializer
        return RecipeWriteSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipe = serializer.save(author=request.user)
        read_serializer = RecipeReadSerializer(recipe)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=False
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        read_serializer = RecipeReadSerializer(instance)
        return Response(read_serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAdminAuthorOrReadOnly],
        url_path='favorite'
    )
    def favorite(self, request, pk=None):
        """PUT: добавление рецепта в избранное. DELETE: удаление."""
        recipe = get_object_or_404(Recipe, id=pk)
        if request.method == 'POST':
            serializer = FavoriteSerializer(
                data={},
                context={
                    'request': request,
                    'recipe': recipe,
                },
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(
                user=self.request.user,
                recipe=recipe,
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            try:
                favorite = Favorite.objects.get(
                    user=self.request.user,
                    recipe=recipe,
                )
                favorite.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Favorite.DoesNotExist:
                return Response(
                    {"error": "Рецепта нет в избранном"},
                    status=status.HTTP_400_BAD_REQUEST
                )

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
        response = HttpResponse(text_content, content_type='text/plain')
        response['Content-Disposition'] = setting_response
        return response

    @action(detail=True, methods=['get'], url_path='get-link')
    def generate_short_link(self, request, pk=None):
        """Генерация короткой ссылки."""
        recipe = self.get_object()
        serializer = ShortLinkSerializer(recipe, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

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


class UserViewSet(viewsets.ModelViewSet):
    """Вьюсет для работы с пользователями и подписками."""

    queryset = User.objects.all()
    http_method_names = ['get', 'post', 'put', 'delete']

    def get_queryset(self):
        if self.action == 'subscriptions':
            return self.request.user.follower.all()
        return super().get_queryset()

    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        return UserSerializer

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

    @action(detail=False, methods=['post'], url_path='set_password')
    def set_password(self, request):
        """Смена пароля."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        methods=['put', 'delete'],
        detail=False,
        url_path='me/avatar',
        permission_classes=[IsAdminAuthorOrReadOnly]
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
        if request.method == "DELETE":
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
        serializer = FollowDetailSerializer(
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
            serializer = FollowSerializer(
                data={},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save(user=user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        elif request.method == 'DELETE':
            follow = request.user.follower.filter(following=following).first()
            if not follow:
                return Response(
                    {"error": "Подписки нет"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            follow.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class ShortLinkRedirectView(View):
    """VeiwSet для редирект по короткой ссылки."""

    def get(self, request, short_id):
        recipe = get_object_or_404(Recipe, short_id=short_id)
        return redirect(f'/recipes/{recipe.id}/')
