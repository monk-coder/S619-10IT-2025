# animations/base_animations.py
import time
import random
from abc import ABC, abstractmethod

class BaseAnimation(ABC):
    def __init__(self):
        self.animation_delays = {
            'fast': 0.3,
            'medium': 0.5,
            'slow': 0.8
        }

    @abstractmethod
    def create_animation(self, *args, **kwargs):
        pass

    def get_dynamic_delay(self, current_frame, total_frames):
        """Динамические задержки для анимации"""
        if current_frame < total_frames - 3:
            return self.animation_delays['fast']
        elif current_frame < total_frames - 1:
            return self.animation_delays['medium']
        else:
            return self.animation_delays['slow']