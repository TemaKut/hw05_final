import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django import forms
from django.core.cache import cache
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow
from posts.constants import NUM_PAGE, TEST_PAGE_2


User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestPostViews(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        image = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=image,
            content_type='image/gif',
        )
        cls.author = User.objects.create_user(username='Artem')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание')
        cls.post = Post.objects.create(
            author=cls.author,
            text=('Тестовый пост для тестирования'),
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text='Test Comment',
        )
        cls.index = 'posts:home'
        cls.group_post = 'posts:group'
        cls.profile = 'posts:profile'
        cls.post_id = 'posts:post_detail'
        cls.create = 'posts:post_create'
        cls.edit = 'posts:post_edit'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.create_user(username='test_user')
        self.authorized_client = Client()
        self.author_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client.force_login(self.author)
        self.follower_us = User.objects.create_user(username='Follower')
        self.follower = Client()
        self.follower.force_login(self.follower_us)

    def check_add_post_in_context(self, obj_1):
        """Этот метод проверяет на соответствие
        объекты поста в БД и соответствующем контексте. на входе необходимо
        указать объект из БД а так же объект из контекста view."""
        obj_2 = self.post
        self.assertEqual(obj_1.id, obj_2.id)
        self.assertEqual(obj_1.text, obj_2.text)
        self.assertEqual(obj_1.group, obj_2.group)
        self.assertEqual(obj_1.author.username, obj_2.author.username)
        self.assertEqual(obj_1.image, obj_2.image)

    def test_correct_templates(self):
        """URL использует нужный шаблон."""
        cache.clear()
        url_templates = {reverse(self.index): 'posts/index.html',
                         reverse(self.create): 'posts/create_post.html',
                         reverse(self.group_post,
                                 kwargs={'slug': self.group.slug}):
                         'posts/group_list.html',
                         reverse(self.profile, kwargs={'username': self.author.username}):
                         'posts/profile.html',
                         reverse(self.post_id,
                                 kwargs={'post_id': self.post.pk}):
                         'posts/post_detail.html',
                         reverse(self.edit,
                                 kwargs={'post_id': self.post.pk}):
                         'posts/create_post.html'}
        for reverse_name, template in url_templates.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_context(self):
        """Шаблон index с правильным контекстом."""
        cache.clear()
        response = self.client.get(reverse(self.index))
        first_obj = response.context['page_obj'].object_list[0]
        self.check_add_post_in_context(first_obj)

    def test_group_posts_context(self):
        """Шаблон group_list с правильным контекстом."""
        response = self.client.get(reverse(
            self.group_post, kwargs={'slug': self.group.slug}))
        first_obj = response.context['page_obj'].object_list[0]
        self.check_add_post_in_context(first_obj)
        context_group = response.context['group']
        self.assertEqual(context_group.slug, self.group.slug)

    def test_profile_context(self):
        """Шаблон profile с правильным контекстом."""
        response = self.client.get(reverse(
            self.profile, kwargs={'username': self.author.username}))
        first_obj = response.context['page_obj'].object_list[0]
        self.check_add_post_in_context(first_obj)
        author = response.context['author']
        self.assertEqual(author.username, self.author.username)
        following = response.context['following']
        self.assertEqual(following, False)

    def test_post_detail_context(self):
        """Шаблон post_detail  с правильным контекстом."""
        response = self.client.get(
            reverse(self.post_id, kwargs={'post_id': self.post.pk}))
        first_obj = response.context['post_valid']
        self.check_add_post_in_context(first_obj)
        comments = response.context['comments'][0]
        self.assertEqual(comments.text, self.comment.text)
        self.assertEqual(comments.author, self.comment.author)
        self.assertEqual(comments.post, self.comment.post)
        self.assertEqual(comments.id, self.comment.id)

    def test_create_context(self):
        """Шаблон post_create с правильным контекстом."""
        response = self.authorized_client.get(reverse(self.create))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField}
        for field, field_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, field_type)

    def test_post_edit_context(self):
        """Шаблон post_edit  с правильным контекстом."""
        response = self.author_client.get(reverse(
            self.edit, kwargs={'post_id': self.post.pk}))
        form_fields = {'text': forms.fields.CharField,
                       'group': forms.fields.ChoiceField}
        for field, field_type in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, field_type)
        is_edit = response.context['is_edit']
        self.assertEqual(is_edit, True)

    def test_new_post_in_pages(self):
        """Пост не попадает в ненужную группу."""
        self.group = Group.objects.create(
            title='Неправильная группа',
            slug='wrong',
            description='Не та группа')
        response = self.client.get(reverse(
            self.group_post, kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['page_obj'].paginator.count, 0)
        Post.objects.create(
            author=TestPostViews.author,
            text='Тестовый пост для тестирования неверной группы',
            group=TestPostViews.group)
        cache.clear()
        response = self.client.get(reverse(
            self.group_post, kwargs={'slug': self.group.slug}))
        self.assertEqual(response.context['page_obj'].paginator.count, 0)
        responses = (self.client.get(reverse(self.index)),
                     self.client.get(reverse(
                         self.group_post, kwargs={'slug': 'test_slug'})),
                     self.client.get(reverse(
                         self.profile, kwargs={'username': self.author.username})))
        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(response.context['page_obj'].paginator.count,
                                 2)

    def test_paginators(self):
        """Выводится правильное количество постов."""
        cache.clear()
        postss = (
            (Post(author=self.author,
                  text=f'Тестовый пост {i}',
                  group=self.group,
                  ))for i in range(NUM_PAGE + TEST_PAGE_2 - 1)
        )

        self.post = Post.objects.bulk_create(list(postss))

        responses = (self.client.get(reverse(self.index)),
                     self.client.get(reverse(
                         self.group_post,
                         kwargs={'slug': self.group.slug})),
                     self.client.get(reverse(
                         self.profile,
                         kwargs={'username': self.author.username})))

        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj'].object_list),
                                 NUM_PAGE)

        responses = (self.client.get(reverse(self.index) + '?page=2'),
                     self.client.get(reverse(
                         self.group_post,
                         kwargs={'slug': 'test_slug'}) + '?page=2'),
                     self.client.get(reverse(
                         self.profile,
                         kwargs={'username': self.author.username}) + '?page=2'))

        for response in responses:
            with self.subTest(response=response):
                self.assertEqual(len(response.context['page_obj'].object_list),
                                 TEST_PAGE_2)

    def test_index_page_used_cache(self):
        """ Тестируем использование кэша на главной странице. """
        cache.clear()
        item_bef_post = self.authorized_client.get(
            reverse('posts:home')).content
        cache.clear()
        new_post = Post.objects.create(
            text='Тестируем кеш',
            author=self.user,
            group=self.group,
        )
        item_with_post = self.authorized_client.get(
            reverse('posts:home')).content
        new_post.delete()
        item_with_cached_post = self.authorized_client.get(
            reverse('posts:home')).content
        cache.clear()
        content_post_deleted_cash_cleared = self.authorized_client.get(
            reverse('posts:home')).content
        self.assertEqual(item_bef_post,
                         content_post_deleted_cash_cleared)
        self.assertEqual(item_with_post, item_with_cached_post)
        self.assertNotEqual(item_with_post,
                            content_post_deleted_cash_cleared)
        self.assertNotEqual(item_bef_post, item_with_cached_post)

    def test_authorized_user_follow(self):
        """ Может ли авторизованный пользователь подписываться. """
        user = User.objects.get(username='test_user')
        follow_count_1 = Follow.objects.filter(user=user).count()
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author.username}))
        follow_count_2 = Follow.objects.filter(user=user).count()
        self.assertEqual(follow_count_1 + 1, follow_count_2)

    def test_authorized_user_unfollow(self):
        """ Может ли авторизованный пользователь отписываться. """
        user = User.objects.get(username='test_user')
        self.authorized_client.get(
            reverse('posts:profile_follow', kwargs={'username': self.author.username}))
        follow_count_1 = Follow.objects.filter(user=user).count()
        self.authorized_client.get(
            reverse('posts:profile_unfollow', kwargs={'username': self.author.username}))
        follow_count_2 = Follow.objects.filter(user=user).count()
        self.assertEqual(follow_count_1 - 1, follow_count_2)

    def test_work_profile_follower(self):
        """ Тестируем попадает ли пост в ленту подписавшихся. """
        self.follower.get(
            reverse('posts:profile_follow', kwargs={'username': self.author.username}))
        response = self.follower.get(reverse('posts:follow_index'))
        count_obj_bef = len(response.context['page_obj'].object_list)
        post_create = Post.objects.create(
            author=self.author,
            text=('Тестовый пост!'),
        )
        response_2 = self.follower.get(reverse('posts:follow_index'))
        count_obj_awt = len(response_2.context['page_obj'].object_list)
        self.assertEqual(count_obj_bef + 1, count_obj_awt)
        post = response_2.context['page_obj'].object_list[0]
        self.assertEqual(post_create.id, post.id)
        self.assertEqual(post_create.text, post.text)
        self.assertEqual(post_create.group, post.group)
        self.assertEqual(post_create.author.username, post.author.username)
        self.assertEqual(post_create.image, post.image)

    def test_work_prifile_not_follower(self):
        """ Тестируем не попадает ли пост в ленту не подписавшихся. """
        response = self.authorized_client.get(reverse('posts:follow_index'))
        count_obj_bef = len(response.context['page_obj'].object_list)
        Post.objects.create(
            author=self.author,
            text=('Тестовый пост!'),
        )
        response_2 = self.follower.get(reverse('posts:follow_index'))
        count_obj_awt = len(response_2.context['page_obj'].object_list)
        self.assertEqual(count_obj_bef, count_obj_awt)

    def test_comment_authorized_user(self):
        """ Проверяем может ли авторизованный пользователь
        оставлять комментарии. """
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        count_comment_bef = len(response.context['comments'])
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Test Comment authorized_client',
        )
        count_comment_after = len(response.context['comments'])
        self.assertEqual(count_comment_bef, count_comment_after)

    def test_comment_guest_user(self):
        """ Тестируем невозможность оставлять комментарии гостем. """
        response = self.client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        count_comment_bef = len(response.context['comments'])
        comment = Comment.objects.create(
            post=self.post,
            author=self.user,
            text='Test Comment authorized_client 2',
        )
        count_comment_after = len(response.context['comments'])
        self.assertEqual(count_comment_bef, count_comment_after)
