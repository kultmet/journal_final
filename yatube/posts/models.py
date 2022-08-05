from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()


class Post(models.Model):
    """Создает пост."""

    text = models.TextField(
        help_text={'create': 'Напишите', 'edit': 'Редактируйте'}
    )
    pub_date = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts')
    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост')
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        return self.text[:settings.POST_LIMITER]


class Group(models.Model):
    """Создает группу."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self):
        return self.title


class Comment(models.Model):
    """Создает комментарий."""
    post = models.ForeignKey(
        Post,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

        def __str__(self):
            return self.text


class Follow(models.Model):
    """Добавляем возможность подписки на авторов."""
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )
