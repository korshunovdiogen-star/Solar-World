from PIL import Image
from io import BytesIO
from django.conf import settings


def optimize_image(
    image,
    width=getattr(settings, "IMAGE_OPTIMIZER_WIDTH", 800),
    height=getattr(settings, "IMAGE_OPTIMIZER_HEIGHT", None),
    quality=getattr(settings, "IMAGE_OPTIMIZER_QUALITY", 80),
):
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
                target_size = (img.width * target_scaler, img.height * target_scaler)
                img.thumbnail(target_size, Image.LANCZOS)
        elif width:
            if img.width > width:
                target_size = (width, (width / img.width) * img.height)
                img.thumbnail(target_size, Image.LANCZOS)
        elif height:
            if img.height > height:
                target_size = ((height / img.height) * img.width, height)
                img.thumbnail(target_size, Image.LANCZOS)

        output = BytesIO()
        img.save(output, format="WEBP", quality=quality, optimize=True)
        output.seek(0)

        return output
