from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст'
        )
        cls.post = Post.objects.create(
            text='Какой то текст',
            author=cls.user,
        )
        cls.not_author = User.objects.create_user(
            username='not_author'
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)
        self.templates_names_public_page = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse(
                'posts:group_list', args=(PostURLTests.group.slug,)
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', args=(PostURLTests.user.username,)
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=(PostURLTests.post.pk,)
            ): 'posts/post_detail.html',
        }
        self.templates_names_private_page = {
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', args=(PostURLTests.post.pk,)
            ): 'posts/create_post.html',
        }

    def test_urls_uses_correct_template_in_public(self):
        """URL-адрес использует соответствующий шаблон."""
        for name, template in self.templates_names_public_page.items():
            with self.subTest(reverse_name=name):
                response = self.client.get(name)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_in_private(self):
        """Тестируем публичные страници, на соответствие шаблонам."""
        for name, template in self.templates_names_private_page.items():
            with self.subTest(reverse_name=name):
                response = self.authorized_client.get(name)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_at_desired_location_public(self):
        """Публичная страшица построилась."""
        for address in self.templates_names_public_page.keys():
            response = self.client.get(address, follow=True)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_at_desired_location_private(self):
        """Приватная страница построилась."""
        for address in self.templates_names_private_page.keys():
            response = self.authorized_client.get(address, follow=True)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_not_authorized_client_in_create(self):
        """Тест create не авторизованого пользователя.
        Редирект на страницу login."""
        response = self.client.get(
            reverse('posts:post_create'), follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_redirect_for_not_authorized_in_post_edit(self):
        """Тест edit не авторизованого пользователя.
        Редирект на страницу login."""
        response = self.client.get(
            reverse(
                'posts:post_edit', args=(PostURLTests.post.pk,)
            ), follow=True
        )
        next = f'?next=/posts/{PostURLTests.post.pk}/edit/'
        redirect = f'/auth/login/{next}'
        self.assertRedirects(
            response, (redirect)
        )

    def test_redirect_for_not_post_author_in_post_edit(self):
        """Тест edit не автор Редирект на post_detail."""
        response = self.not_author_client.get(
            reverse(
                'posts:post_edit', args=(PostURLTests.post.pk,)
            ), follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(PostURLTests.post.pk,)
        ))

    def test_404_url_exists_at_desired_location(self):
        """Страници нетю Ошибка 404."""
        response = self.client.get('/unexisting/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
