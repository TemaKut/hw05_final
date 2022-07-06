from django.core.paginator import Paginator

from .constants import NUM_PAGE


def _help_paginator(request, posts, num=NUM_PAGE):
    """Paginator func."""
    paginator = Paginator(posts, num)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj
