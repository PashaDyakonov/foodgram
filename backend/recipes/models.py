from django.core.validators import MinValueValidator
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

import recipes.constants as constants


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
        verbose_name='Логин',
        help_text='Укажите логин пользователя',
        validators=[UnicodeUsernameValidator()],
        unique=True,
    )
    email = models.EmailField(
        max_length=constants.EMAIL_MAX_LENGTH,
        verbose_name='Электронная почта',
        unique=True,
        help_text='Укажите адрес электронной почты',
    )
    first_name = models.CharField(
        max_length=constants.FIRST_NAME_MAX_LENGTH,
        verbose_name='Имя',
        help_text='Укажите имя',
        blank=True
    )
    last_name = models.CharField(
        max_length=constants.LAST_NAME_MAX_LENGTH,
        verbose_name='Фамилия',
        help_text='Укажите фамилию',
        blank=True
    )
    avatar = models.ImageField(
        upload_to='users/avatars/',
        verbose_name='Аватар',
        help_text='Загрузите аватара'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        ordering = ('username',)
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Follow(models.Model):
    """Модель для хранения подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='followers',
        help_text='Кто подписан'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='authors',
        help_text='Пользователь, на которого подписываются'
    )

    class Meta:
        ordering = ('user__username',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_author'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f'{self.user.username} - {self.following.username}'


class Tag(models.Model):
    """Модель для тегов."""

    name = models.CharField(
        max_length=32,
        unique=True,
        verbose_name='Название',
        help_text='Введите название тега'
    )
    slug = models.SlugField(
        unique=True,
        max_length=32,
        verbose_name='Уникальный идентификатор (slug)',
        help_text='Введите URL-адрес'
    )

    class Meta:
        ordering = ('slug',)
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return self.name


class Ingredients(models.Model):
    """Модель для ингридиентов."""

    name = models.CharField(
        max_length=128,
        verbose_name='Название ингредиента',
        help_text='Введите название ингредиента'
    )
    measurement_unit = models.CharField(
        max_length=64,
        verbose_name='Единица измерения',
        help_text='Введите единицу измерения'
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='recipes',
        help_text='Укажите автора',
        verbose_name='Автор'
    )
    name = models.CharField(
        max_length=constants.MAX_LENGTH_NAME_RECIPE,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        upload_to='recipe/images/',
        verbose_name='Изображение',
        help_text='Добавьте изображение к рецепту'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredients,
        verbose_name='Ингридиенты',
        help_text='Выберите ингридиенты для рецепта',
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги',
        help_text='Выберите теги',
    )
    cooking_time = models.PositiveIntegerField(
        validators=[MinValueValidator(constants.MIN_TIME_COOKING)],
        verbose_name='Время готовки',
        help_text='Укажите время готовки от {constants.MIN_TIME_COOKING} мин.',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.author.username} - {self.name}'


class RecipeIngredient(models.Model):
    """Модель для указание количества ингридиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        help_text='Укажите рецепт',
        verbose_name='Рецепт'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        related_name='recipe_ingredients',
        help_text='Укажите ингредиент',
        verbose_name='Ингредиент'
    )
    amount = models.CharField(
        validators=[MinValueValidator(constants.INGREDIENT_AMOUNT_MIN)],
        max_length=10,
        help_text='Укажите количество',
        verbose_name='Количество'
    )

    class Meta:
        ordering = ('recipe',)
        verbose_name = 'Ингридиент в рецепте'
        verbose_name_plural = 'Ингридиенты в рецепте'

    def __str__(self):
        return (f'{self.recipe.name} - {self.ingredient.name} -'
                f'{self.amount} {self.ingredient.measurement_unit}')


class Favorite(models.Model):
    """Модель для добавления в избранное."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text='Пользователь устанавливается автоматически',
        verbose_name='Пользователь',
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorites',
        help_text='Укажите рецепт, чтобы добавить в избранное',
        verbose_name='Избранное',
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite'
            )
        ]

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingList(models.Model):
    """Модель списка покупки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Покупатель',
        help_text='Укажите покупателя',
    )
    recipe = models.ManyToManyField(
        Recipe,
        verbose_name='Рецепты',
        related_name='shopping_carts',
        help_text='Выберите рецепты для покупки ингридиентов',
    )

    class Meta:
        ordering = ('user',)
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_shopping_list'
            )
        ]

    def __str__(self):
        """Возвращает строковое представление списка покупок."""
        return self.user.username
