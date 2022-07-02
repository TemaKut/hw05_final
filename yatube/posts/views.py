from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from .utils import paginator
from django.views.decorators.cache import cache_page


def _get_post_objects():
    """Получаем объекты модели пост."""
    result = Post.objects.select_related('author', 'group').all()

    return result


@cache_page(20)
def index(request):
    """Вывод главной страницы с постами."""
    posts = _get_post_objects()
    context = {
        'page_obj': paginator(request, posts),
    }

    return render(request, "posts/index.html", context)


def group_posts(request, slug):
    """Вывод страницы с постами конкретной группы."""
    group = Group.objects.get(slug=slug)
    posts = group.posts.all()

    context_group = {
        'group': group,
        'page_obj': paginator(request, posts),
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
        'page_obj': paginator(request, posts),
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
    form = PostForm(request.POST or None, files=request.FILES or None,)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()

        return redirect('posts:profile', username=request.user.username)

    return render(request, "posts/create_post.html", {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница редактирования созданного ранее поста."""
    post_obj = Post.objects.select_related('author', 'group').get(id=post_id)
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
            {'is_edit': True, 'form': form, },
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
    authors = Follow.objects.filter(user=request.user).values('author')
    posts = Post.objects.select_related(
        'author', 'group').filter(author__in=authors)

    context = {
        'page_obj': paginator(request, posts),
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """ Подписаться на автора. """
    follower = User.objects.get(username=request.user)
    author = get_object_or_404(User, username=username)
    y_n = Follow.objects.filter(user=follower, author=author)

    if follower != author and len(y_n) == 0:
        Follow.objects.create(
            user=follower,
            author=author,
        )

        return redirect('posts:follow_index')

    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    """ Отписаться от автора. """
    follower = User.objects.get(username=request.user)
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=follower, author=author).delete()
    return redirect('posts:follow_index')
