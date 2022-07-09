from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import help_paginator


def _get_post_objects():
    """Получаем объекты модели пост."""
    result = Post.objects.select_related('author', 'group')

    return result


@cache_page(20)
def index(request):
    """Вывод главной страницы с постами."""
    posts = _get_post_objects()
    context = {
        'page_obj': help_paginator(request, posts),
    }

    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """Вывод страницы с постами конкретной группы."""
    group = Group.objects.get(slug=slug)
    posts = group.posts.all()

    context_group = {
        'group': group,
        'page_obj': help_paginator(request, posts),
    }

    return render(request, "posts/group_list.html", context_group)


def profile(request, username):
    """Вывод страницы с постами конкретного пользователя."""
    user = get_object_or_404(User, username=username)
    posts = user.posts.all()
    following = request.user.is_authenticated and Follow.objects.filter(
        user=request.user, author=user).exists()

    context_profile = {
        'author': user,
        'page_obj': help_paginator(request, posts),
        'following': following,
    }

    return render(request, "posts/profile.html", context_profile)


def post_detail(request, post_id):
    """Вывод информации о конкретном посте."""
    post_valid = get_object_or_404(Post, id=post_id)
    comments = post_valid.comments.all()
    form = CommentForm()
    context_detail = {
        'post_valid': post_valid,
        'form': form,
        'comments': comments,
    }

    return render(request, "posts/post_detail.html", context_detail)


@login_required
def post_create(request):
    """Страница создания поста."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, "posts/create_post.html", {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования созданного ранее поста."""
    post_obj = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None,
                    instance=post_obj,
                    )
    if request.user == post_obj.author and post_obj:
        if request.method == 'POST' and form.is_valid():
            form.author = request.user
            form.save()

            return redirect(
                'posts:post_detail',
                post_id=post_id,
            )

        return render(
            request,
            "posts/create_post.html",
            {'is_edit': True, 'form': form},
        )

    return redirect(
        'posts:post_detail',
        post_id=post_id,
    )


@login_required
def add_comment(request, post_id):
    """View функция для отображения комментариев к постам."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()

    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """ Страница с постами интересных пользователей. """
    posts = Post.objects.select_related(
        'author', 'group').filter(author__following__user=request.user)

    context = {
        'page_obj': help_paginator(request, posts),
    }

    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """ Подписаться на автора. """
    author = get_object_or_404(User, username=username)
    author_is_followed = Follow.objects.filter(
        user=request.user, author=author).exists()

    if request.user != author and not author_is_followed:
        Follow.objects.create(
            user=request.user,
            author=author,
        )

    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """ Отписаться от автора. """
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()

    return redirect('posts:follow_index')
