SECRET_KEY = "test"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "optimizer_middleware",
]
MIDDLEWARE = [
    "optimizer_middleware.middleware.ImageOptimizationMiddleware",
]
