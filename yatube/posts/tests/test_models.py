from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_text_field(self):
        """Проверяем, что у модели Post корректно работает __str__."""
        post = PostModelTest.post
        self.assertEqual(post.text[:settings.TEST_LIMITER], str(post))

    def test_models_group_title_field(self):
        """Проверяем работоспособность модели Group."""
        group = PostModelTest.group
        self.assertEqual(group.title, 'Тестовая группа')
