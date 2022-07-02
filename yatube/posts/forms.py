from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    """Форма для редактирования и создания поста."""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')


class CommentForm(forms.ModelForm):
    """Форма для создания комментария."""

    class Meta:
        model = Comment
        fields = (
            'text',
        )
