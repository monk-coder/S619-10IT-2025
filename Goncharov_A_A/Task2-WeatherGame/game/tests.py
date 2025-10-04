import json
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from . import config
from .models import CitySearchHistory, PlayerState, PlayerUpgrade, WeatherTask


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
        PlayerUpgrade.objects.create(user=self.user, upgrade_key="task_slot", level=1)
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

    def test_task_creation_prevents_duplicates(self):
        PlayerUpgrade.objects.create(user=self.user, upgrade_key="task_slot", level=1)
        payload = {"city": "Москва", "title": "Зонтик"}
        url = reverse("game:api_tasks")
        first = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(first.status_code, 200)
        duplicate = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(duplicate.status_code, 400)
        self.assertIn("существ", duplicate.json()["error"].lower())

    def test_game_progress_rejects_large_jump(self):
        url = reverse("game:api_game_progress")
        payload = {"current_floor": config.MAX_FLOOR_ABSOLUTE + 1, "floors_travelled": 0}
        response = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("этаж", response.json()["error"].lower())

    def test_reset_progress_clears_state(self):
        state = PlayerState.objects.get(user=self.user)
        state.current_floor = 42
        state.coins = 999
        state.total_floors_travelled = 120
        state.save(update_fields=["current_floor", "coins", "total_floors_travelled", "updated_at"])

        PlayerUpgrade.objects.create(user=self.user, upgrade_key="task_slot", level=2)
        WeatherTask.objects.create(user=self.user, city="Москва", title="Зонтик", notes="")
        CitySearchHistory.objects.create(user=self.user, city="Москва")

        url = reverse("game:api_game_reset")
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        payload = response.json()["data"]
        self.assertEqual(payload["currentFloor"], 0)
        self.assertEqual(payload["coins"], 0)
        self.assertEqual(payload["totalFloorsTravelled"], 0)
        self.assertFalse(PlayerUpgrade.objects.filter(user=self.user).exists())
        self.assertFalse(WeatherTask.objects.filter(user=self.user).exists())
        self.assertFalse(CitySearchHistory.objects.filter(user=self.user).exists())
        new_state = PlayerState.objects.get(user=self.user)
        self.assertEqual(new_state.current_floor, 0)
        self.assertEqual(new_state.coins, 0)
        self.assertEqual(new_state.total_floors_travelled, 0)


class LoginViewTests(TestCase):
    def setUp(self) -> None:
        self.user = User.objects.create_user(username="loginuser", email="login@example.com", password="pass12345")

    def test_login_rejects_invalid_password(self):
        url = reverse("game:login")
        response = self.client.post(url, {"email": "login@example.com", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, "Неверный email или пароль", html=False)

    def test_login_with_valid_credentials(self):
        url = reverse("game:login")
        response = self.client.post(url, {"email": "login@example.com", "password": "pass12345"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("game:index"))

    def test_logout_via_post(self):
        self.client.login(username="loginuser", password="pass12345")
        response = self.client.post(reverse("game:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("game:login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)
