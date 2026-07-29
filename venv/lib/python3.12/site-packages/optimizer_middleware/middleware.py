import os
from io import BytesIO

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

# On latter updates use the below and deprricate the resize_and_optimize function
# from .utils import optimize_image

DEFAULT_WIDTH = getattr(settings, "IMAGE_OPTIMIZER_WIDTH", 800)
DEFAULT_HEIGHT = getattr(settings, "IMAGE_OPTIMIZER_HEIGHT", None)
DEFAULT_QUALITY = getattr(settings, "IMAGE_OPTIMIZER_QUALITY", 80)


class ImageOptimizationMiddleware:
    """Middleware to optimize uploaded images before they are saved."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method in ["POST", "PUT", "PATCH"] and request.FILES:
            width = request.META.get("IMAGE_OPTIMIZER_WIDTH", DEFAULT_WIDTH)
            height = request.META.get("IMAGE_OPTIMIZER_HEIGHT", DEFAULT_HEIGHT)
            quality = request.META.get("IMAGE_OPTIMIZER_QUALITY", DEFAULT_QUALITY)

            for field_name, file in request.FILES.items():
                if file.content_type.startswith("image/"):  # Process only images
                    optimized_image = self.resize_and_optimize(
                        file, width, height, quality
                    )
                    optimized_file = InMemoryUploadedFile(
                        optimized_image,  # File content
                        field_name,  # Field name
                        os.path.splitext(file.name)[0] + ".webp",  # New filename
                        "image/webp",  # MIME type
                        optimized_image.tell(),  # File size
                        None,  # Encoding
                    )
                    request.FILES[field_name] = optimized_file  # Replace original file

            if hasattr(request, "data") and isinstance(request.data, dict):
                for field_name in request.FILES.keys():
                    if field_name in request.data:
                        request.data[field_name] = request.FILES[field_name]

        return self.get_response(request)

    def resize_and_optimize(self, image, width=None, height=None, quality=80):
        """Resize and optimize an image before saving."""
        with Image.open(image) as img:
            # Convert mode only if necessary
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # Efficient resizing using thumbnail() (preserves aspect ratio)
            # prevent scaling up
            if width and height:
                if img.width > width and img.height > height:
                    target_scaler = max(width / img.width, height / img.height)
                    target_size = (
                        img.width * target_scaler,
                        img.height * target_scaler,
                    )
                    img.thumbnail(target_size, Image.LANCZOS)
            elif width:
                if img.width > width:
                    target_size = (width, (width / img.width) * img.height)
                    img.thumbnail(target_size, Image.LANCZOS)
            elif height:
                if img.height > height:
                    target_size = ((height / img.height) * img.width, height)
                    img.thumbnail(target_size, Image.LANCZOS)

            # Save to memory in WebP format
            output = BytesIO()
            img.save(output, format="WEBP", quality=quality, optimize=True)
            output.seek(0)

            return output
