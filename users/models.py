from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    test_results = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"Профиль пользователя {self.user.username}"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Создаёт профиль сразу после регистрации пользователя"""
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Сохраняет профиль вместе с пользователем"""
    instance.profile.save()

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'content_type', 'object_id')  # один пользователь не может добавить один объект дважды

    def __str__(self):
        return f"{self.user.username} -> {self.content_object}"


class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='history')
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']  # сначала новые
        unique_together = ('user', 'content_type', 'object_id')  # чтобы не дублировать записи

    def __str__(self):
        return f"{self.user.username} -> {self.content_object} ({self.viewed_at})"