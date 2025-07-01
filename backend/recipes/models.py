from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import shortuuid

import recipes.constants as constants


User = get_user_model()


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
        verbose_name='URL-адерс',
        help_text='Введите URL-адрес'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'{self.name}'


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
        ordering = ['-id']
        verbose_name = 'Ингридиент'
        verbose_name_plural = 'Ингридиенты'

    def __str__(self):
        return f'{self.name} - {self.measurement_unit}'


class Recipe(models.Model):
    """Модель для рецептов."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text='Укажите автора',
        verbose_name='Автор',
        related_name='recipes'
    )
    name = models.CharField(
        max_length=constants.MAX_LENGTH_NAME_RECIPE,
        verbose_name='Название рецепта',
        help_text='Введите название рецепта'
    )
    image = models.ImageField(
        upload_to='recipe/images/',
        verbose_name='Изображение',
        help_text='Добавитье изображение к рецепту'
    )
    text = models.TextField(
        verbose_name='Описание',
        help_text='Введите описание рецепта',
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
        related_name='recipes'
    )
    cooking_time = models.PositiveIntegerField(
        validators=[
            MinValueValidator(constants.MIN_TIME_COOKING),
            MaxValueValidator(constants.MAX_TIME_COOKING)
        ],
        verbose_name='Время готовки',
        help_text='Укажите время готовки в минутах от 1 минуты до 24ч',
    )
    short_id = models.CharField(
        max_length=constants.MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        null=True,
        verbose_name='Сокращенная ссылка',
        help_text='Сокращенная ссылка на рецепт'
    )

    class Meta:
        ordering = ('-id',)
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.author.username} - {self.name}'

    def save(self, *args, **kwargs):
        if not self.short_id:
            self.short_id = shortuuid.ShortUUID().random(length=6)
        super().save(*args, **kwargs)

    def get_short_url(self, request=None):
        if request:
            return request.build_absolute_uri(f'/r/{self.short_id}/')
        return f'/r/{self.short_id}/'


class RecipeIngredient(models.Model):
    """Модель для указание количества ингридиента в рецепте."""

    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        help_text='Укажите рецепт',
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    ingredient = models.ForeignKey(
        Ingredients,
        on_delete=models.CASCADE,
        help_text='Укажите ингредиент',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(constants.INGREDIENT_AMOUNT_MIN),
            MaxValueValidator(constants.INGREDIENT_AMOUNT_MAX)
        ],
        help_text='Укажите количество',
        verbose_name='Количество'
    )

    class Meta:
        ordering = ['-id']
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
        help_text='Пользователь устанавливается автоматически',
        verbose_name='Пользователь',
        related_name='favorites'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        help_text='Укажите рецепт, чтобы добавить в избранное',
        verbose_name='Избранное',
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        unique_together = ('user', 'recipe')

    def __str__(self):
        return f'{self.user.username} - {self.recipe.name}'


class ShoppingList(models.Model):
    """Модель списка покупки."""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='shopper',
        verbose_name='Покупатель',
        help_text='Укажите покупателя',
    )
    recipe = models.ManyToManyField(
        Recipe,
        verbose_name='Рецепты',
        help_text='Выберите рецепты для покупки ингридиентов',
        related_name='in_shopping_lists'
    )

    class Meta:
        ordering = ['-id']
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Списки покупок'
        unique_together = ('user',)

    def __str__(self):
        """Возвращает строковое представление списка покупок."""
        return f'{self.user.username} '
