from django.shortcuts import render
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from .models import Product, Category
from .serializers import ProductSerializer
from solarWorld.utils import parse_page_number
import logging
import json

logger = logging.getLogger(__name__)

def shop_page(request):
    categories = dict(
        Category.objects.order_by('name').values_list('slug', 'name')
    )
    return render(request, 'shop/shop_catalog.html', {
        'category_options_json': json.dumps(categories, ensure_ascii=False),
    })

# Карта сортировки для товаров
SORT_MAP = {
    'name_asc': 'name',
    'name_desc': '-name',
    'price_asc': 'price',
    'price_desc': '-price',
    'stock_asc': 'stock',
    'stock_desc': '-stock',
    'category_asc': 'category__name',
    'category_desc': '-category__name',
}

@cache_page(60 * 15)
def shop_api(request):
    q = request.GET.get('q', '').strip()
    category_slug = request.GET.get('category', 'all') 
    categories = dict(
        Category.objects.order_by('name').values_list('slug', 'name')
    )
    ordering = request.GET.get('ordering', 'name_asc')
    page = parse_page_number(request.GET.get('page', 1))
    per_page = 12

    page = max(1, page)

    queryset = Product.objects.filter(available=True)

    # Поиск по названию
    if q:
        queryset = queryset.filter(name__icontains=q)

    # Фильтрация по категории (если не 'all')
    if category_slug != 'all':
        try:
            category = Category.objects.get(slug=category_slug)
            queryset = queryset.filter(category=category)
        except Category.DoesNotExist:
            return JsonResponse({
                'results': [],
                'total_pages': 1,
                'current_page': page,
            })

    # Сортировка
    sort_field = SORT_MAP.get(ordering, 'name')
    queryset = queryset.order_by(sort_field)

    # Пагинация
    paginator = Paginator(queryset, per_page)
    total_pages = paginator.num_pages
    page = min(page, total_pages) if total_pages > 0 else 1
    page_obj = paginator.get_page(page)
    items = page_obj.object_list

    # Сериализация
    serializer = ProductSerializer(items, many=True, context={'request': request})

    return JsonResponse({
        'results': serializer.data,
        'total_pages': total_pages,
        'current_page': page,
    })

@cache_page(60 * 60) 
def category_options(request):

    options = dict(
        Category.objects.order_by('name').values_list('slug', 'name')
    )
    return JsonResponse(options)