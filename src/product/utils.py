from django.core.paginator import Paginator
from django.core.paginator import EmptyPage
from django.core.paginator import PageNotAnInteger


def paginate_data(queryset, page, size):
    paginator = Paginator(queryset, size)
    page_obj = paginator.get_page(page)

    return page_obj


def get_variant_id(productvariants, tag):
    for item in productvariants:
        if tag in item['tags']:
            return item['variant']
    return 0