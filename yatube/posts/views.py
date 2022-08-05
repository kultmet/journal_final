from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Follow, Post, Group, Comment, User
from .utils import paginator


@cache_page(20, key_prefix='main_page')
def index(request):
    post_list = Post.objects.select_related('author', 'group')
    page_obj = paginator(request, post_list, settings.LIMITED)
    context = {
        'page_obj': page_obj,
        'index': True
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    page_obj = paginator(request, posts, settings.LIMITED)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.order_by('-pub_date')
    page_obj = paginator(request, posts, settings.LIMITED)
    following = (
        request.user.is_authenticated and author != request.user
        and Follow.objects.filter(user=request.user, author=author)
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST  or None)
    comments = Comment.objects.select_related('post').filter(post=post)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post_form = form.save(commit=False)
        post_form.author = request.user
        form.save()
        return redirect('posts:profile', request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id=post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id=post_id)
    context = {
        'post': post,
        'form': form,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginator(request, post_list, settings.LIMITED)
    context = {
        'page_obj': page_obj,
        'follow': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.filter(
        user=request.user
    )
    if request.user != author and not following:
        Follow.objects.create(
            author=author, user=request.user
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    following = author.following.filter(
        user=request.user
    )
    if request.user != author and following:
        Follow.objects.get(
            author=author, user=request.user
        ).delete()
    return redirect('posts:profile', username)
