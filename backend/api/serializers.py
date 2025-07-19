from collections import Counter

from django.contrib.auth import get_user_model
from djoser.serializers import UserSerializer as DjoserUserSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.constants import INGREDIENT_AMOUNT_MIN, MIN_TIME_COOKING
from recipes.models import (
    Favorite,
    Ingredients,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)


User = get_user_model()


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = '__all__'


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredients
        fields = '__all__'


class RecipeIngredientsWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи количества."""

    id = serializers.PrimaryKeyRelatedField(
        queryset=Ingredients.objects.all(),
    )
    amount = serializers.IntegerField(min_value=INGREDIENT_AMOUNT_MIN)

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeIngredientReadSerializer(serializers.ModelSerializer):
    """Сериализатор для чтения с полем amount."""

    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measurement_unit'
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed', 'avatar')

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return user.followers.filter(
            user=request.user).exists() if request else False


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления автара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой записий рецепта."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields


class FollowUserSerializer(UserSerializer):
    """Сериализатор для отображения данных пользователя при подписке."""

    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(source='recipes.count')

    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ('recipes', 'recipes_count')

    def get_recipes(self, author):
        recipes = author.recipes.all()
        if recipes_limit := self.context['request'].GET.get('recipes_limit'):
            return ShortRecipeSerializer(
                recipes[:int(recipes_limit)],
                many=True,
                context=self.context
            ).data
        return ShortRecipeSerializer(
            recipes,
            many=True,
            context=self.context).data


class RecipeReadSerializer(serializers.ModelSerializer):
    """Сериализатор для вывода рецептов."""

    author = UserSerializer(read_only=True)
    ingredients = RecipeIngredientReadSerializer(
        many=True,
        source='recipe_ingredients'
    )
    tags = TagSerializer(read_only=True, many=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'name',
            'is_favorited',
            'is_in_shopping_cart',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time',
        )

    def check_user_status(self, obj, model):
        user = self.context.get('request')
        return (
            user.user.is_authenticated
            and model.objects.filter(
                recipe=obj,
                user=user.user
            ).exists()
        )

    def get_is_favorited(self, obj):
        return self.check_user_status(obj, Favorite)

    def get_is_in_shopping_cart(self, obj):
        return self.check_user_status(obj, ShoppingList)


class RecipeWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для изменения рецептов."""

    ingredients = RecipeIngredientsWriteSerializer(
        many=True,
        allow_empty=False
    )
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True
    )
    image = Base64ImageField()
    cooking_time = serializers.IntegerField(
        min_value=MIN_TIME_COOKING,
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'text',
            'ingredients',
            'tags',
            'cooking_time'
        )

    def _validate_no_duplicates(self, items, item_name, id_extractor=None):
        """Общий метод для проверки дубликатов."""
        if not items:
            raise serializers.ValidationError(
                f'Добавьте хотя бы один {item_name}.'
            )
        duplicates = [
            item_id for item_id, count
            in Counter(
                [
                    id_extractor(item)for item in items
                ]
                if id_extractor else items).items() if count > 1
        ]

        if duplicates:
            raise ValidationError({
                item_name: (
                    f'Найдены дублирующиеся {item_name}: '
                    f'{duplicates}'
                )
            }, code=f'duplicate_{item_name}')
        return items

    def validate_tags(self, value):
        return self._validate_no_duplicates(
            value, 'тег', id_extractor=lambda tag: tag.id
        )

    def validate_ingredients(self, value):
        return self._validate_no_duplicates(
            value,
            'ингредиент',
            id_extractor=lambda ingredient: ingredient['id']
        )

    @staticmethod
    def create_recipe_ingredients_bulk(instance, ingredients_data):
        RecipeIngredient.objects.bulk_create(
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        )

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_recipe_ingredients_bulk(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
