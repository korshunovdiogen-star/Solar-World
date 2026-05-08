from functools import wraps
from django.contrib.contenttypes.models import ContentType
from users.models import History, Favorite
from django.utils import timezone


def track_user_activity  (model_class):
    def decorator (detal_view):
        @wraps(detal_view)
        def wrapper(request, pk):
            is_favorite = False

            if request.user.is_authenticated:
                content_type = ContentType.objects.get_for_model(model_class)
                is_favorite = Favorite.objects.filter(user=request.user, content_type=content_type, object_id=pk).exists()
                History.objects.update_or_create(
                    user=request.user,
                   content_type=content_type,
                    object_id=pk,
                  defaults={'viewed_at': timezone.now()}
              )
            return detal_view(request, pk, is_favorite=is_favorite)
        return wrapper
    return decorator