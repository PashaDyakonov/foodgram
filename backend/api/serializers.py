from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
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
from users.models import Follow


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
        error_messages={
            'does_not_exist': 'Ингредиент с ID {pk_value} не существует.',
            'incorrect_type': 'ID ингредиента должно быть числом.'
        }
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
        read_only_fields = ('id', 'name', 'measurement_unit', 'amount')


class UserSerializer(DjoserUserSerializer):
    """Сериализатор для пользователя."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('is_subscribed',)

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return user.follower.filter(
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
        read_only_fields = ('id', 'name', 'image', 'cooking_time')


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


class FollowSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки."""

    class Meta:
        model = Follow
        fields = '__all__'
        read_only_fields = ['user', 'following']

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


class FavoriteSerializer(serializers.ModelSerializer):
    """Сериализатор для добавление в избранное."""

    class Meta:
        model = Favorite
        fields = ('recipe',)
        read_only_fields = ['recipe']

    def validate(self, data):
        """Проверка на дубликат."""
        request = self.context.get('request')
        if request.user.favorites.filter(
            recipe=self.context.get('recipe')
        ).exists():
            raise serializers.ValidationError(
                "Рецепт уже в избранном"
            )
        return data

    def to_representation(self, instance):
        return ShortRecipeSerializer(
            instance.recipe,
            context=self.context
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для список покупок."""

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
        read_only_fields = ['user', 'recipe']

    def validate(self, data):
        request = self.context.get('request')
        recipe_id = request.parser_context['kwargs']['pk']
        recipe = get_object_or_404(Recipe, id=recipe_id)
        shopping_list, _ = ShoppingList.objects.get_or_create(
            user=request.user
        )
        if request.method == 'POST':
            if shopping_list.recipe.filter(id=recipe.id).exists():
                raise serializers.ValidationError(
                    {"error": "Рецепт уже в списке покупок!"}
                )
        elif request.method == 'DELETE':
            if not shopping_list.recipe.filter(id=recipe.id).exists():
                raise serializers.ValidationError(
                    {"error": "Рецепта нет в списке покупок"}
                )
        data.update({
            'shopping_list': shopping_list,
            'recipe': recipe
        })
        return data


class DownloadShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для скачивание список покупок."""

    ingredients = serializers.SerializerMethodField()
    user = serializers.SlugRelatedField(
        read_only=True,
        default=serializers.CurrentUserDefault(),
        slug_field='username'
    )

    class Meta:
        model = ShoppingList
        fields = ('id', 'user', 'ingredients')

    def get_ingredients(self, obj):
        recipes = obj.recipe.all()
        ingredient_dict = {}
        for recipe in recipes:
            for recipe_ingredient in recipe.recipe_ingredients.all():
                ingredient = recipe_ingredient.ingredient
                key = (
                    ingredient.id,
                    ingredient.name,
                    ingredient.measurement_unit
                )
                if key in ingredient_dict:
                    ingredient_dict[key] += recipe_ingredient.amount
                else:
                    ingredient_dict[key] = recipe_ingredient.amount
        return [
            {
                'id': key[0],
                'name': key[1],
                'measurement_unit': key[2],
                'amount': amount
            }
            for key, amount in ingredient_dict.items()
        ]


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

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег.'
            )

        seen = set()
        duplicates = []
        for tag in value:
            if tag in seen:
                duplicates.append(tag)
            else:
                seen.add(tag)

        if duplicates:
            raise serializers.ValidationError(
                'Найдены дублирующиеся теги: '
                f'{", ".join(str(tag) for tag in duplicates)}'
            )

        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )

        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            duplicates = {
                x for x in ingredient_ids if ingredient_ids.count(x) > 1
            }
            raise ValidationError(
                {
                    'ingredients': (
                        'Найдены дублирующиеся ингредиенты: '
                        f'{", ".join(map(str, duplicates))}'
                    )
                },
                code='duplicate_ingredients'
            )
        return value

    @staticmethod
    def create_recipe_ingredients_bulk(instance, ingredients_data):
        RecipeIngredient.objects.bulk_create([
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = super().create(validated_data)
        recipe.tags.set(tags_data)
        self.create_recipe_ingredients_bulk(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        instance.tags.set(tags_data)
        instance.ingredients.clear()
        self.create_recipe_ingredients_bulk(instance, ingredients_data)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeReadSerializer(instance, context=self.context).data
