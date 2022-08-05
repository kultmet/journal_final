from django.core.paginator import Paginator


def paginator(request, post_object, limit):
    paginator = Paginator(post_object, limit)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
