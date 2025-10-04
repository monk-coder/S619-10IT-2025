import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from . import config
from .models import CitySearchHistory, PlayerState, WeatherTask


User = get_user_model()


class GameApiTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="tester", email="tester@example.com", password="secret123")
        self.client = Client()
        self.client.login(username="tester", password="secret123")

    def test_player_state_created(self):
        state = PlayerState.objects.get(user=self.user)
        self.assertEqual(state.current_floor, 0)
        self.assertEqual(state.coins, 0)

    def test_game_progress_awards_coins(self):
        url = reverse("game:api_game_progress")
        response = self.client.post(
            url,
            data=json.dumps({"current_floor": 5, "floors_travelled": 5}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        expected = 5 * config.COINS_PER_FLOOR
        self.assertEqual(data["coins"], expected)

    def test_weather_lookup_requires_coins(self):
        url = reverse("game:api_weather_lookup")
        response = self.client.post(
            url,
            data=json.dumps({"city": "Москва"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Недостаточно", response.json()["error"])

    @mock.patch("game.views.get_weather")
    def test_weather_lookup_success(self, mock_weather):
        mock_weather.return_value = {
            "weather": [{"description": "ясно", "icon": "01d"}],
            "main": {"temp": 10, "feels_like": 8, "humidity": 50, "pressure": 1000},
            "wind": {"speed": 3},
        }
        state = PlayerState.objects.get(user=self.user)
        state.coins = config.WEATHER_LOOKUP_PRICE
        state.save(update_fields=["coins"])

        url = reverse("game:api_weather_lookup")
        response = self.client.post(
            url,
            data=json.dumps({"city": "Москва"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["coins"], 0)
        self.assertEqual(payload["weather"]["city"], "Москва")
        self.assertTrue(CitySearchHistory.objects.filter(user=self.user, city="Москва").exists())

    def test_tasks_crud_flow(self):
        create_url = reverse("game:api_tasks")
        payload = {"city": "Москва", "title": "Взять зонт", "notes": "проверить шторм"}
        response = self.client.post(create_url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 200)
        task_id = response.json()["data"]["task"]["id"]

        update_url = reverse("game:api_task_detail", args=[task_id])
        response = self.client.patch(
            update_url,
            data=json.dumps({"status": "done"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        task = WeatherTask.objects.get(id=task_id)
        self.assertEqual(task.status, "done")

        response = self.client.delete(update_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(WeatherTask.objects.filter(id=task_id).exists())
from django.test import TestCase

# Create your tests here.
