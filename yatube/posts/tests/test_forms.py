import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Post, Group, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.not_author = User.objects.create_user(username='not_author')
        self.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='текстовый текст'
        )
        self.post = Post.objects.create(
            text='какой-то текст',
            author=self.user,
            group=self.group,
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.not_author_client = Client()
        self.not_author_client.force_login(self.not_author)

    def test_create_post_for_authorized_client(self):
        """Тестируем создани поста, авторизованым пользователем."""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'еще один дополнительный пост',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_post.text, form_data['text'])
        self.assertEqual(new_post.author, self.user)
        self.assertEqual(new_post.group, self.group)
        self.assertEqual(new_post.image, f'posts/{form_data["image"]}')
        self.assertRedirects(
            response, reverse(
                'posts:profile', args=(self.user.username,)
            )
        )

    def test_create_post_for_not_authorized(self):
        """Тестируем создани поста, не авторизованым пользователем."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'еще один дополнительный пост',
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        login_url = reverse('users:login')
        url = reverse('posts:post_create')
        self.assertRedirects(response, f'{login_url}?next={url}')

    def test_edit_post_for_author(self):
        """Тестируем редактинование поста, автором поста."""
        my_post = Post.objects.create(
            text='мой пост',
            author=self.user
        )
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_01.gif',
            content=small_gif,
            content_type='image/gif'
        )
        new_text = 'добавить еще текст'
        form_data = {
            'text': new_text,
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', args=(my_post.pk,)
            ),
            data=form_data,
            follow=True
        )
        my_post.refresh_from_db()
        self.assertEqual(Post.objects.count(), post_count)
        self.assertEqual(my_post.text, form_data['text'])
        self.assertEqual(
            my_post.author, self.user
        )
        self.assertEqual(my_post.group, self.group)
        self.assertEqual(my_post.image, f'posts/{form_data["image"]}')
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(my_post.pk,)
        ))

    def test_edit_post_for_not_author(self):
        """Тестируем редактирование поста, не автором."""
        his_post = Post.objects.create(
            text='его пост',
            author=self.user
        )
        post_count = Post.objects.count()
        new_text = 'добавить еще текст'
        form_data = {
            'text': new_text,
            'group': self.group.pk,
        }
        response = self.not_author_client.post(
            reverse('posts:post_edit', args=(his_post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(his_post.pk,)
        ))


class CommetTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='auth')
        self.post = Post.objects.create(
            text='Я виражаю свои мысли.',
            author=self.user
        )
        self.commentator = User.objects.create_user(username='toxic')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.commentator)

    def test_only_authorized_users_can_comment_on_posts(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'А мне плевать на твои мысли!',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        new_comment = Comment.objects.first()
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(new_comment.text, form_data['text'])
        self.assertRedirects(
            response, reverse('posts:post_detail', args=(self.post.pk,))
        )

    def test_only_not_authorized_users_can_comment_on_posts(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'А мне плевать на твои мысли!',
        }
        response = self.client.post(
            reverse('posts:add_comment', args=(self.post.pk,)),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count)
        login_url = reverse('users:login')
        url = reverse('posts:add_comment', args=(self.post.pk,))
        self.assertRedirects(response, f'{login_url}?next={url}')
