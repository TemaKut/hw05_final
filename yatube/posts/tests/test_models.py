from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тестируем модель поста на 15 символов поста и название группы."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='TestGroupTitle',
            slug='TestSlug',
            description='TestDescription',
        )
        cls.post = Post.objects.create(
            text='а' * 30,
            author=cls.user,
        )

    def test_str_post_and_group(self):
        """Корректность отображения метода str при обращении
        к модели post и group."""
        post = PostModelTest.post
        group = PostModelTest.group
        group_title = group.title
        fields_str = {
            'а' * 15: str(post),
            group_title: str(group),
        }
        for field, str_ in fields_str.items():
            with self.subTest(field=field):
                self.assertEqual(field, str_)

    def test_post_verbose_name(self):
        """Тест на наличие VN в посте."""
        post = PostModelTest.post
        field_verboses = {
            'author': 'Автор поста',
            'group': 'Группа',
        }
        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)
