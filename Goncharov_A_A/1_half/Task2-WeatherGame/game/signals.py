from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import PlayerState

User = get_user_model()


@receiver(post_save, sender=User)
def ensure_player_state(sender, instance: User, created: bool, **kwargs) -> None:
    if created:
        PlayerState.objects.create(user=instance)
