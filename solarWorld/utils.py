from django.core.paginator import Paginator
from django.http import JsonResponse

ITEMS_PER_PAGE = 12


def parse_page_number(value, default=1):
    try:
        page = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, page)


def paginate(items, page, per_page=ITEMS_PER_PAGE):
    paginator = Paginator(items, per_page)
    total_pages = max(1, paginator.num_pages)
    current_page = min(page, total_pages)
    return list(paginator.get_page(current_page).object_list), total_pages, current_page


def paginated_json_response(items, page, serialize, per_page=ITEMS_PER_PAGE):
    page_items, total_pages, current_page = paginate(items, page, per_page)
    return JsonResponse(
        {
            "results": serialize(page_items),
            "total_pages": total_pages,
            "current_page": current_page,
        }
    )


def search_and_sort(queryset, query, sort_map, ordering, default="name"):
    if query:
        queryset = queryset.filter(name__icontains=query)
    return queryset.order_by(sort_map.get(ordering, default))
