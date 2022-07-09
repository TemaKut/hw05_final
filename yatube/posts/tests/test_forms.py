import shutil
import tempfile

from django.test import TestCase, Client, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestFormEfficiency(TestCase):
    """Проверяем формы."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Artem')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title="Test title",
            slug="TestSlug",
            description="Test description",
        )
        cls.P_POST_DETAIL = 'posts:post_detail'
        cls.P_PROFILE = 'posts:profile'
        cls.P_POST_EDIT = 'posts:post_edit'
        cls.P_CREATE = 'posts:post_create'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_create_by_authorized_user(self):
        """Проверяем возможность создания поста
        авторизованным пользователем запись в БД."""
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
            'text': 'Test Text',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(self.P_CREATE),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            self.P_PROFILE, kwargs={'username': self.user.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        object_post = Post.objects.reverse().first()
        text = object_post.text
        group = object_post.group
        author = object_post.author.username
        image = object_post.image
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group, self.group)
        self.assertEqual(author, self.user.username)
        self.assertEqual(image.name, 'posts/' + uploaded.name)

    def test_post_edit_by_author(self):
        """Происходит ли изменение поста
        авторизованным автором в базе данных."""
        post = Post.objects.create(
            text="Test text 1",
            author=self.user,
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
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Test Text Changed',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse(self.P_POST_EDIT, args=(str(post.id))),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            self.P_POST_DETAIL, args=(str(post.id))))
        self.assertEqual(Post.objects.count(), post_count)
        object_post = Post.objects.get(id=str(post.id))
        text = object_post.text
        group = object_post.group
        author = object_post.author.username
        image = object_post.image
        self.assertEqual(text, form_data['text'])
        self.assertEqual(group, self.group)
        self.assertEqual(author, self.user.username)
        self.assertEqual(image.size, uploaded.size)
