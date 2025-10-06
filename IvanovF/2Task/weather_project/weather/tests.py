import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import SearchHistory, WeatherTask, WeatherSnapshot


class TestWeatherTaskApi(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="secret123")
        self.other_user = User.objects.create_user(username="bob", password="secret123")
        self.tasks_url = reverse("tasks_collection")
        self.logout_url = reverse("logout_user")

    def authenticate(self):
        self.client.login(username="alice", password="secret123")

    def test_tasks_require_authentication(self):
        response = self.client.get(self.tasks_url)
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())

    def test_create_list_update_delete_task_flow(self):
        self.authenticate()

        create_payload = {"city": "Москва", "text": "Взять зонт"}
        response = self.client.post(
            self.tasks_url,
            data=json.dumps(create_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        task_id = data["task"]["id"]
        self.assertEqual(data["task"]["city"], create_payload["city"])
        self.assertEqual(WeatherTask.objects.filter(user=self.user).count(), 1)

        list_response = self.client.get(self.tasks_url)
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()["tasks"]), 1)

        detail_url = reverse("task_detail", args=[task_id])
        update_payload = {"city": "Сочи", "text": "Крем от солнца"}
        update_response = self.client.patch(
            detail_url,
            data=json.dumps(update_payload),
            content_type="application/json",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["task"]["city"], update_payload["city"])

        delete_response = self.client.delete(detail_url)
        self.assertEqual(delete_response.status_code, 200)
        self.assertTrue(delete_response.json()["ok"])
        self.assertFalse(WeatherTask.objects.filter(id=task_id).exists())

    def test_cannot_access_foreign_task(self):
        task = WeatherTask.objects.create(user=self.other_user, city="Париж", text="Теплый шарф")

        self.authenticate()
        detail_url = reverse("task_detail", args=[task.id])

        self.assertEqual(self.client.get(detail_url).status_code, 404)
        self.assertEqual(
            self.client.patch(
                detail_url,
                data=json.dumps({"city": "Москва", "text": "Новое"}),
                content_type="application/json",
            ).status_code,
            404,
        )
        self.assertEqual(self.client.delete(detail_url).status_code, 404)

    def test_history_is_scoped_to_authenticated_user(self):
        history_url = reverse("get_history")
        self.assertEqual(self.client.get(history_url).json(), {"entries": []})

        SearchHistory.objects.create(user=self.user, city="Москва")
        SearchHistory.objects.create(user=self.other_user, city="Париж")

        self.authenticate()
        data = self.client.get(history_url).json()
        self.assertEqual(len(data["entries"]), 1)
        self.assertEqual(data["entries"][0]["city"], "Москва")

    def test_logout_endpoint(self):
        self.authenticate()
        response = self.client.post(self.logout_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["ok"])
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(self.tasks_url).status_code, 401)
        self.assertEqual(self.client.get(self.logout_url).status_code, 405)


class TestWeatherCaching(TestCase):
    def setUp(self):
        self.url = reverse("get_weather")

    def _mock_api_response(self, city="Москва", temp=12, rh=55, description="Ясно", icon="c01d"):
        payload = {
            "data": [
                {
                    "temp": temp,
                    "rh": rh,
                    "weather": {"description": description, "icon": icon},
                }
            ]
        }
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = payload
        return response

    @patch("weather.views.requests.get")
    def test_weather_fetch_creates_snapshot(self, mock_get):
        mock_get.return_value = self._mock_api_response()

        response = self.client.get(f"{self.url}?city=Москва")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["cached"])
        self.assertEqual(WeatherSnapshot.objects.count(), 1)
        mock_get.assert_called_once()

    @patch("weather.views.requests.get")
    def test_weather_uses_cache_within_two_hours(self, mock_get):
        WeatherSnapshot.objects.create(
            city="Москва",
            normalized_city="москва",
            payload={
                "city": "Москва",
                "temperature": 10,
                "humidity": 50,
                "description": "Ясно",
                "icon": "https://www.weatherbit.io/static/img/icons/c01d.png",
            },
            fetched_at=timezone.now(),
        )

        response = self.client.get(f"{self.url}?city=Москва")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["cached"])
        mock_get.assert_not_called()

    @patch("weather.views.requests.get")
    def test_weather_refreshes_after_two_hours(self, mock_get):
        stale_time = timezone.now() - timedelta(hours=3)
        snapshot = WeatherSnapshot.objects.create(
            city="Москва",
            normalized_city="москва",
            payload={
                "city": "Москва",
                "temperature": 10,
                "humidity": 50,
                "description": "Ясно",
                "icon": "https://www.weatherbit.io/static/img/icons/c01d.png",
            },
            fetched_at=stale_time,
        )

        mock_get.return_value = self._mock_api_response(temp=5, description="Дождь", icon="r01d")

        response = self.client.get(f"{self.url}?city=Москва")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["cached"])
        self.assertLess(stale_time, WeatherSnapshot.objects.get(id=snapshot.id).fetched_at)
        mock_get.assert_called_once()


class TestCurrencyEndpoint(TestCase):
    def setUp(self):
        self.url = reverse("get_currency")

    def test_requires_key(self):
        with patch("weather.views.API_KEY_CURRENCY", new=None):
            response = self.client.get(f"{self.url}?base=USD&symbols=EUR")
        self.assertEqual(response.status_code, 500)

    def test_validation(self):
        with patch("weather.views.API_KEY_CURRENCY", new="key"):
            response = self.client.get(self.url)
        self.assertEqual(response.status_code, 400)
        with patch("weather.views.API_KEY_CURRENCY", new="key"):
            response = self.client.get(f"{self.url}?base=usd")
        self.assertEqual(response.status_code, 400)

    @patch("weather.views.requests.get")
    def test_fetch_currency_rates(self, mock_get):
        mock_get.return_value = MagicMock(
            status_code=200,
            json=MagicMock(return_value={"data": {"EUR": 0.9, "RUB": 92.0}}),
        )
        with patch("weather.views.API_KEY_CURRENCY", new="key"), patch("weather.views.API_URL_CURRENCY", new="https://curr.test/latest"):
            response = self.client.get(f"{self.url}?base=USD&symbols=EUR,RUB")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["base"], "USD")
        self.assertIn("EUR", data["rates"])
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "https://curr.test/latest")
        self.assertEqual(kwargs["params"], {"base_currency": "USD", "currencies": "EUR,RUB"})
        self.assertEqual(kwargs["headers"], {"apikey": "key"})
