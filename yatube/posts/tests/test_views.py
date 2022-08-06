from random import randint
import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Post, Group, Follow
from posts.forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='test_image.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Какой то текст',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded,
        )
        cls.fail_group = Group.objects.create(
            title='Не та группа',
            slug='fail-group',
            description='Не тот некстовый текст',
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    def for_test_context_page_obj(self, first_object):
        """Вспомогательная функция для тестирования словаря context."""
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_pk_0 = first_object.pk
        post_image_0 = first_object.image
        fields = {
            post_text_0: PostPagesTest.post.text,
            post_pub_date_0: PostPagesTest.post.pub_date,
            post_author_0: PostPagesTest.post.author,
            post_group_0: PostPagesTest.post.group,
            post_pk_0: PostPagesTest.post.pk,
            post_image_0: PostPagesTest.post.image
        }
        for key, value in fields.items():
            return self.assertEqual(key, value)

    def test_main_page_show_correct_context(self):
        """Шаблон Index сформирован и правильным контекстом."""
        response = self.client.get(reverse('posts:main_page'))
        self.assertIn('page_obj', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, PostPagesTest.post)
        self.for_test_context_page_obj(first_post)

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:group_list', args=(
                PostPagesTest.group.slug,
            ))
        )
        self.assertIn('group', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['group'], PostPagesTest.group)
        self.assertEqual(response.context['page_obj'][0], PostPagesTest.post)
        self.for_test_context_page_obj(response.context['page_obj'][0])

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.client.get(
            reverse('posts:profile', args=(
                PostPagesTest.post.author,
            ))
        )
        self.assertIn('author', response.context)
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['author'], PostPagesTest.post.author)
        self.assertEqual(response.context['page_obj'][0], PostPagesTest.post)
        self.for_test_context_page_obj(response.context['page_obj'][0])

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.client.get(
                reverse(
                    'posts:post_detail', args=(
                        PostPagesTest.post.pk,
                    )
                )
            )
        )
        self.assertIn('post', response.context)
        requested_post = response.context['post']
        self.assertEqual(
            requested_post, PostPagesTest.post
        )
        self.assertEqual(
            requested_post.image, PostPagesTest.post.image
        )

    def test_post_create_and_edit_show_correct_context(self):
        """В шаблон  post_edit передается правильный контекст."""
        addresses = [
            reverse('posts:post_edit', args=(
                PostPagesTest.post.pk,
            )),
            reverse('posts:post_create'),
        ]
        for address in addresses:
            response = self.authorized_client.get(address)
            self.assertIn('form', response.context)
            self.assertIsInstance(
                response.context.get('form'), PostForm
            )
            if 'is_edit' in response.context:
                self.assertTrue(
                    response.context.get('is_edit'), True
                )
            if 'post' in response.context:
                self.assertEqual(
                    response.context['post'], PostPagesTest.post
                )

    def test_created_post_in_group_all_list_pages(self):
        """Тестируем как происходит магия. Забыл заклятие."""
        pages_and_group = {
            reverse('posts:main_page'): PostPagesTest.group,
            reverse('posts:group_list', args=(
                PostPagesTest.group.slug,
            )): PostPagesTest.group,
            reverse('posts:profile', args=(
                PostPagesTest.user.username,
            )): PostPagesTest.group,
        }
        for reverse_name, group in pages_and_group.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                self.assertEqual(first_object.group, group)

    def test_created_post_not_in_group(self):
        """Тестируем, что обьект не попал в другую группу."""
        response = self.authorized_client.get(reverse('posts:main_page'))
        first_object = response.context['page_obj'][0]
        self.assertNotEqual(first_object.group, PostPagesTest.fail_group)


class PaginatorViewsTest(TestCase):

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.posts = Post.objects.bulk_create(
            Post(
                text=f'{i}', author=self.user, group=self.group
            )for i in range(
                1, randint(settings.LIMITED + 2, settings.LIMITED * 2)
            )
        )
        self.addresses = [
            reverse('posts:main_page'),
            reverse('posts:group_list', args=(
                self.group.slug,
            )),
            reverse('posts:profile', args=(
                self.user.username,
            )),
        ]

    def test_first_page_contains_record_for_all_public_page(self):
        """Тестируем первую и последнюю страници пагинатора."""
        for address in self.addresses:
            with self.subTest(address=address):
                response = self.client.get(address, {'page': 1})
                self.assertEqual(
                    len(
                        response.context['page_obj']
                    ), settings.LIMITED
                )
                response = self.client.get(address, {'page': 2})
                self.assertEqual(
                    len(
                        response.context['page_obj']
                    ), len(self.posts) - settings.LIMITED
                )


class CachePagesTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='auth')
        self.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст')
        self.post = Post.objects.create(
            text='Новый пост',
            author=self.user
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_for_main_page(self):
        """Кеш для main_page работает."""
        post = Post.objects.create(
            text='Новый пост, сомнительного содержания',
            author=self.user
        )
        response = self.authorized_client.get(reverse('posts:main_page'))
        self.assertEqual(response.context['page_obj'][0], post)
        Post.objects.get(pk=post.pk).delete()
        response1 = self.authorized_client.get(reverse('posts:main_page'))
        self.assertEqual(response1.content, response.content)
        cache.clear()
        response2 = self.authorized_client.get(reverse('posts:main_page'))
        self.assertNotEqual(response2.content, response.content)


class FollowTest(TestCase):
    """Тестируем подписчиков."""
    def setUp(self):
        self.author = User.objects.create_user(username='auth')
        self.user = User.objects.create_user(username='not_auth')
        self.not_follower = User.objects.create_user(
            username='not_follower'
        )
        self.post = Post.objects.create(
            text='какой то текст', author=self.author
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_follower_client = Client()
        self.not_follower_client.force_login(self.not_follower)

    def test_follow_for_authorized_user(self):
        """Тест Подписки для авторизованого пользователя."""
        follow_count = Follow.objects.filter(
            user=self.user, author=self.author
        ).count()
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.author.username,)))
        get_follow = Follow.objects.filter(user=self.user, author=self.author)
        self.assertEqual(get_follow.count(), follow_count + 1)

    def test_unfollow_for_authorized_user(self):
        """Отписки для авторизованого пользователя."""
        Follow.objects.create(user=self.user, author=self.author)
        follow_count = Follow.objects.filter(
            user=self.user, author=self.author
        ).count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', args=(self.author.username,)))
        get_follow = Follow.objects.filter(user=self.user, author=self.author)
        self.assertEqual(get_follow.count(), follow_count - 1)

    def test_following_for_not_authorized_user(self):
        """Тест подписок для не авторизованого пользователя."""
        response = self.client.get(
            reverse('posts:profile_follow', args=(self.author.username,))
        )
        login_url = reverse('users:login')
        url = reverse('posts:profile_follow', args=(self.author.username,))
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_post_visibility_for_follower(self):
        """Тест видимости постов, подписчикам."""
        Follow.objects.create(user=self.user, author=self.author)
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertEqual(response.context['page_obj'][0], self.post)

    def test_post_invisibility_for_not_follower(self):
        """Тест невидимости постов, для неподписаных пользователей."""
        Follow.objects.create(user=self.user, author=self.author)
        response = self.not_follower_client.get(
            reverse('posts:follow_index')
        )
        expected_result = 0
        self.assertEqual(
            len(response.context['page_obj']), expected_result
        )

    def test_not_following_to_myself(self):
        """Тест Подписка на самого себя, невозможно."""
        follow_count = Follow.objects.filter(
            user=self.user, author=self.user
        ).count()
        self.authorized_client.get(
            reverse('posts:profile_follow', args=(self.user.username,)))
        get_follow = Follow.objects.filter(user=self.user, author=self.user)
        self.assertEqual(get_follow.count(), follow_count)
