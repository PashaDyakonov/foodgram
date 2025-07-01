import base64
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from recipes.models import (
    Favorite,
    Ingredients,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)
from recipes.constants import (
    INGREDIENT_AMOUNT_MIN,
    INGREDIENT_AMOUNT_MAX,
    MIN_TIME_COOKING,
    MAX_TIME_COOKING,
)
from users.models import Follow
from users.constants import PAGE_SIZE


User = get_user_model()


class Base64ImageField(serializers.ImageField):
    """Сериализатор для фотографии в BASE64."""

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]

            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
        return super().to_internal_value(data)


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для тегов."""

    class Meta:
        model = Tag
        fields = (
            'id', 'name', 'slug'
        )


class IngredientsSerializer(serializers.ModelSerializer):
    """Сериализатор для ингредиентов."""

    class Meta:
        model = Ingredients
        fields = (
            'id', 'name', 'measurement_unit'
        )


class RecipeIngredientsWriteSerializer(serializers.ModelSerializer):
    """Сериализатор для записи количества."""

    id = serializers.IntegerField()
    amount = serializers.IntegerField(
        min_value=INGREDIENT_AMOUNT_MIN,
        max_value=INGREDIENT_AMOUNT_MAX
    )

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


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.follower.filter(user=request.user).exists()
        return False


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователей."""

    password = serializers.CharField(
        write_only=True,
        validators=[validate_password]
    )

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )
        extra_kwargs = {
            'email': {'required': True, 'allow_blank': False},
            'first_name': {'required': True, 'allow_blank': False},
            'last_name': {'required': True, 'allow_blank': False}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Сериализатор для смены пароля."""
    current_password = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password]
    )

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Текущий пароль неверный")
        return value


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления автара."""

    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)
        extra_kwargs = {
            'avatar': {'required': True, 'allow_blank': False},
        }


class ShortRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для краткой записий рецепта."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class FollowDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для полного вывода подписки."""

    email = serializers.ReadOnlyField(source='following.email')
    id = serializers.ReadOnlyField(source='following.id')
    username = serializers.ReadOnlyField(source='following.username')
    first_name = serializers.ReadOnlyField(source='following.first_name')
    last_name = serializers.ReadOnlyField(source='following.last_name')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = Base64ImageField(source='following.avatar')

    class Meta:
        model = Follow
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
            'avatar',
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return user.following.filter(
            following=obj.following
        ).exists()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit', PAGE_SIZE)
        try:
            limit = int(limit)
        except ValueError:
            pass
        return ShortRecipeSerializer(
            obj.following.recipes.all()[:limit],
            many=True,
            context={'request': request},
        ).data

    def get_recipes_count(self, obj):
        return obj.following.recipes.all().count()


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
        return FollowDetailSerializer(instance, context=self.context).data


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


class ShortLinkSerializer(serializers.ModelSerializer):
    """Сериализатор для получения корроткой ссылки."""

    short_link = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = ['short_link']

    def get_short_link(self, obj):
        request = self.context.get('request')
        return obj.get_short_url(request)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['short-link'] = data.pop('short_link')
        return data


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
    image = Base64ImageField(required=True, allow_null=True)
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
        return bool(
            user
            and user.user.is_authenticated
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
    image = Base64ImageField(required=True, allow_null=True)
    cooking_time = serializers.IntegerField(
        min_value=MIN_TIME_COOKING,
        max_value=MAX_TIME_COOKING
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
        extra_kwargs = {
            'text': {'required': True},
        }

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один тег.'
            )
        if len(value) != len(set(value)):
            raise serializers.ValidationError('Теги не должны повторяться')
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                'Добавьте хотя бы один ингредиент.'
            )
        ingredient_ids = [ingredient['id'] for ingredient in value]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise ValidationError(
                {"ingredients": "Ингредиенты не должны повторяться."},
                code='duplicate_ingredients'
            )
        existing_ids = set(Ingredients.objects.filter(
            id__in=ingredient_ids
        ).values_list('id', flat=True))
        missing_ids = set(ingredient_ids) - existing_ids
        if missing_ids:
            raise serializers.ValidationError(
                {
                    "ingredients": ("Ингредиенты с ID",
                                    f"{missing_ids} не существуют.")
                },
                code='ingredient_not_found'
            )
        return value

    @staticmethod
    def create_recipe_ingredients_bulk(instance, ingredients_data):
        ingredients_to_create = [
            RecipeIngredient(
                recipe=instance,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
            for ingredient_data in ingredients_data
        ]
        RecipeIngredient.objects.bulk_create(ingredients_to_create)

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags_data)
        self.create_recipe_ingredients_bulk(recipe, ingredients_data)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        tags_data = validated_data.pop('tags', None)
        instance = super().update(instance, validated_data)
        if tags_data is not None:
            instance.tags.set(tags_data)
        if ingredients_data is not None:
            instance.ingredients.clear()
            self.create_recipe_ingredients_bulk(instance, ingredients_data)
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if 'ingredients' not in representation or not representation[
            'ingredients'
        ]:
            ingredients = instance.recipe_ingredients.all()
            representation['ingredients'] = RecipeIngredientsWriteSerializer(
                ingredients, many=True).data
        return representation
