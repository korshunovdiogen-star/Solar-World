import io

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from PIL import Image
from rest_framework.parsers import MultiPartParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from optimizer_middleware.middleware import ImageOptimizationMiddleware


def create_test_image():
    image = Image.new("RGB", (1000, 1000), "red")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    return SimpleUploadedFile("test.jpg", buffer.read(), content_type="image/jpeg")

def test_image_optimization():
    rf = RequestFactory()
    img = create_test_image()
    request = rf.post("/", {"file": img}, format="multipart")

    middleware = ImageOptimizationMiddleware(lambda r: r)
    request = middleware(request)  # returns request because get_response=r

    optimized_file = request.FILES["file"]
    assert optimized_file.name.endswith(".webp")
    assert optimized_file.content_type == "image/webp"

def test_drf_image_optimization():
    """Test that the DRF middleware optimizes uploaded images to WebP."""
    rf = APIRequestFactory()
    img = create_test_image()

    # Step 1: Create Django WSGIRequest
    django_request = rf.post("/", {"file": img}, format="multipart")
    
    # Step 2: Pass Django request through middleware
    middleware = ImageOptimizationMiddleware(lambda r: r)
    django_request = middleware(django_request)  # Process the Django request

    # Step 3: Create DRF Request **after middleware**
    drf_request = Request(django_request, parsers=[MultiPartParser()])

    # Step 4: Access drf_request.FILES to trigger parsing
    optimized_file = drf_request.FILES["file"]
    assert optimized_file.name.endswith(".webp")
    assert optimized_file.content_type == "image/webp"

    # Assert DRF request.data points to optimized file
    assert drf_request.data["file"] is drf_request.FILES["file"]

    # Optional: Check that the image can be opened as WebP
    optimized_file.file.seek(0)
    from PIL import Image as PILImage
    with PILImage.open(optimized_file.file) as im:
        assert im.format == "WEBP"