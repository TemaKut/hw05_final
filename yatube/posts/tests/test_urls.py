from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

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
        cls.index = 'posts:home'
        cls.group_post = 'posts:group'
        cls.profile = 'posts:profile'
        cls.post_id = 'posts:post_detail'
        cls.create = 'posts:post_create'
        cls.edit = 'posts:post_edit'
        cls.profile_follow = 'posts:profile_follow'
        cls.profile_unfollow = 'posts:profile_unfollow'
        cls.add_comment = 'posts:add_comment'
        cls.follow_index = 'posts:follow_index'

    def setUp(self):
        self.autorized_user = Client()
        self.autorized_user.force_login(self.user)
        self.not_author = Client()
        self.user_2 = User.objects.create_user(username='Arrrt')
        self.not_author.force_login(self.user_2)

    def test_public_access_url(self):
        """Проврка общей доступности url для гостевого пользователя."""
        url_status = {
            reverse(self.index): HTTPStatus.OK,
            reverse(self.group_post, kwargs={'slug': 'test'}): HTTPStatus.OK,
            reverse(self.profile, kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse(self.post_id, kwargs={'post_id': '1'}): HTTPStatus.OK,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_url_guest(self):
        """ Проверяем редирект гостя со страницы добавления комментариев. """
        response = self.client.get(reverse(self.add_comment, args=('1')))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404_page_guset(self):
        """ Проверяем доступность страницы 404 гостем. """
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_autorized_access_url(self):
        """Проврка доступности url для авторизованного пользователя."""
        url_status = {
            reverse(self.create): HTTPStatus.OK,
            reverse(self.edit, kwargs={'post_id': '1'}): HTTPStatus.OK,
            reverse(self.add_comment, kwargs={'post_id': '1'}): HTTPStatus.FOUND,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.autorized_user.get(url)
                self.assertEqual(response.status_code, status)

    def test_create_edit_unavailability_by_guest(self):
        """Недоступность для гостя (Переадресация)."""
        resp = self.client.get(reverse(self.create))
        self.assertRedirects(
            resp, '/auth/login/?next=%2Fcreate%2F', HTTPStatus.FOUND)

    def test_edit_unavailability_by_not_author(self):
        """Недоступность для не автора (Переадресация)."""
        resp = self.not_author.get(reverse(self.edit, kwargs={'post_id': '1'}))
        self.assertRedirects(
            resp, reverse(self.post_id, kwargs={'post_id': '1'}), HTTPStatus.FOUND)

    def test_post_edit_by_guest(self):
        """Не доступность posts/<int:post_id>/edit/
        для пользователя не являющегося автором."""
        self.user_2 = User.objects.create_user(username='Darya')
        self.user_not_author = Client()
        self.user_not_author.force_login(self.user_2)
        response = self.user_not_author.get(
            reverse(self.edit, kwargs={'post_id': '1'}))
        self.assertRedirects(response, reverse(
            self.post_id, kwargs={'post_id': '1'}), HTTPStatus.FOUND)

    def test_accordance_urls_and_templates(self):
        """Проврка на соответствие урл и шаблонов"""
        url_templates_names = {
            reverse(self.index): 'posts/index.html',
            reverse(self.group_post, kwargs={'slug': 'test'}): 'posts/group_list.html',
            reverse(self.profile, kwargs={'username': self.user.username}): 'posts/profile.html',
            reverse(self.post_id, kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse(self.create): 'posts/create_post.html',
            reverse(self.edit, kwargs={'post_id': '1'}): 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.autorized_user.get(address)
                self.assertTemplateUsed(response, template)
