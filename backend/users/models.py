from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models

import users.constants as constants


class User(AbstractUser):
    """Модель пользователя."""

    username = models.CharField(
        max_length=constants.USERNAME_MAX_LENGTH,
        verbose_name='Логин',
        help_text='Укажите логин пользователя',
        validators=UnicodeUsernameValidator(),
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
    REQUIRED_FIELDS = ['username', email, first_name, last_name]

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
    subscribers = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscribers',
        help_text='Пользователь, на которого подписываются'
    )

    class Meta:
        ordering = ('username',)
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        unique_together = ('user', 'following')

    def __str__(self):
        """Возвращает строковое представление подписки."""
        return f'{self.user.username} - {self.following.username}'
