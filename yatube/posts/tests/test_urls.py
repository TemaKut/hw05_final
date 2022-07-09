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
        cls.P_HOME = 'posts:home'
        cls.P_GROUP = 'posts:group'
        cls.P_PROFILE = 'posts:profile'
        cls.P_POST_DETAIL = 'posts:post_detail'
        cls.P_CREATE = 'posts:post_create'
        cls.P_POST_EDIT = 'posts:post_edit'
        cls.P_PROFILE_FOLLOW = 'posts:profile_follow'
        cls.P_PROFILE_UNFOLLOW = 'posts:profile_unfollow'
        cls.P_ADD_COMMENT = 'posts:add_comment'
        cls.P_FOLLOW_INDEX = 'posts:follow_index'

    def setUp(self):
        self.autorized_user = Client()
        self.autorized_user.force_login(self.user)
        self.not_author = Client()
        self.user_2 = User.objects.create_user(username='Arrrt')
        self.not_author.force_login(self.user_2)

    def test_public_access_url(self):
        """Проврка общей доступности url для гостевого пользователя."""
        url_status = {
            reverse(self.P_HOME): HTTPStatus.OK,
            reverse(self.P_GROUP, kwargs={'slug': self.group.slug}): HTTPStatus.OK,
            reverse(self.P_PROFILE,
                    kwargs={'username': self.user.username}): HTTPStatus.OK,
            reverse(self.P_POST_DETAIL, kwargs={'post_id': self.post.id}): HTTPStatus.OK,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_url_guest(self):
        """ Проверяем статус страницы для гостя. """
        response = self.client.get(
            reverse(self.P_ADD_COMMENT, kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_404_page_guset(self):
        """ Проверяем доступность страницы 404 гостем. """
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_autorized_access_url(self):
        """Проврка доступности url для авторизованного пользователя."""
        url_status = {
            reverse(self.P_CREATE): HTTPStatus.OK,
            reverse(self.P_POST_EDIT, kwargs={'post_id': self.post.id}): HTTPStatus.OK,
        }
        for url, status in url_status.items():
            with self.subTest(url=url):
                response = self.autorized_user.get(url)
                self.assertEqual(response.status_code, status)

    def test_redirect_comment_autorized(self):
        """ Проверяем редирект со страницы добавления комментариев
        для авторизованного пользователя. """
        response = self.autorized_user.get(reverse(self.P_ADD_COMMENT,
                                                   kwargs={'post_id': self.post.id}))
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_edit_unavailability_by_guest(self):
        """Недоступность для гостя (Переадресация)."""
        resp = self.client.get(reverse(self.P_CREATE))
        self.assertRedirects(
            resp, '/auth/login/?next=%2Fcreate%2F', HTTPStatus.FOUND)

    def test_edit_unavailability_by_not_author(self):
        """Недоступность для не автора (Переадресация)."""
        resp = self.not_author.get(
            reverse(self.P_POST_EDIT, kwargs={'post_id': self.post.id}))
        self.assertRedirects(
            resp, reverse(self.P_POST_DETAIL,
                          kwargs={'post_id': self.post.id}), HTTPStatus.FOUND)

    def test_post_edit_by_guest(self):
        """Переадресация с posts/<int:post_id>/edit/
        для пользователя не являющегося автором."""
        self.user_2 = User.objects.create_user(username='Darya')
        self.user_not_author = Client()
        self.user_not_author.force_login(self.user_2)
        response = self.user_not_author.get(
            reverse(self.P_POST_EDIT, kwargs={'post_id': self.post.id}))
        self.assertRedirects(response, reverse(
            self.P_POST_DETAIL, kwargs={'post_id': self.post.id}), HTTPStatus.FOUND)

    def test_accordance_urls_and_templates(self):
        """Проврка на соответствие урл и шаблонов"""
        temp_pos = 'posts/profile.html'
        url_templates_names = {
            reverse(self.P_HOME): 'posts/index.html',
            reverse(self.P_GROUP,
                    kwargs={'slug': self.group.slug}): 'posts/group_list.html',
            reverse(self.P_PROFILE,
                    kwargs={'username': self.user.username}): temp_pos,
            reverse(self.P_POST_DETAIL,
                    kwargs={'post_id': self.post.id}): 'posts/post_detail.html',
            reverse(self.P_CREATE): 'posts/create_post.html',
            reverse(self.P_POST_EDIT,
                    kwargs={'post_id': self.post.id}): 'posts/create_post.html',
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.autorized_user.get(address)
                self.assertTemplateUsed(response, template)
