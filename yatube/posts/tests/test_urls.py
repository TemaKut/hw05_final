from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class GuestURLTest(TestCase):
    """Тест доступности урл для неавторизованного юзера."""

    @classmethod
    def setUpClass(cls):
        """Создаём записи в БД."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='Artem')
        cls.group = Group.objects.create(
            title='TestTitle',
            slug='test',
            description='TestDescription',
        )
        cls.post = Post.objects.create(
            text='TestText',
            author=cls.user,
        )

    def setUp(self):
        self.autorized_user = Client()
        self.autorized_user.force_login(self.user)
        self.not_author = Client()
        self.user_2 = User.objects.create_user(username='Arrrt')
        self.not_author.force_login(self.user_2)

    def test_public_access_url(self):
        """Проврка общей доступности url для гостевого пользователя."""
        url_status = {
            '/': HTTPStatus.OK,
            '/group/test/': HTTPStatus.OK,
            '/profile/Artem/': HTTPStatus.OK,
            '/posts/1/': HTTPStatus.OK,
            '/posts/1/comment/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_autorized_access_url(self):
        """Проврка доступности url для авторизованного пользователя."""
        url_status = {
            '/create/': HTTPStatus.OK,
            '/posts/1/edit/': HTTPStatus.OK,
            '/posts/1/comment/': HTTPStatus.FOUND,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.autorized_user.get(url)
                self.assertEqual(response.status_code, status)

    def test_create_edit_unavailability_by_guest(self):
        """Недоступность для гостя (Переадресация)."""
        resp = self.client.get('/create/')
        self.assertRedirects(
            resp, '/auth/login/?next=%2Fcreate%2F', HTTPStatus.FOUND)

    def test_edit_unavailability_by_not_author(self):
        """Недоступность для не автора (Переадресация)."""
        resp = self.not_author.get('/posts/1/edit/')
        self.assertRedirects(
            resp, '/posts/1/', HTTPStatus.FOUND)

    def test_post_edit_by_guest(self):
        """Не доступность posts/<int:post_id>/edit/
        для пользователя не являющегося автором."""
        self.user_2 = User.objects.create_user(username='Darya')
        self.user_not_author = Client()
        self.user_not_author.force_login(self.user_2)
        response = self.user_not_author.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/', HTTPStatus.FOUND)

    def test_accordance_urls_and_templates(self):
        """Проврка на соответствие урл и шаблонов"""
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/test/': 'posts/group_list.html',
            '/profile/Artem/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.autorized_user.get(address)
                self.assertTemplateUsed(response, template)
