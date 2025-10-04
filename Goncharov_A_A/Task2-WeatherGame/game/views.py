from __future__ import annotations

import json

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.utils import timezone

from . import config
from .forms import RegistrationForm
from .models import (
    CitySearchHistory,
    PlayerState,
    TaskStatus,
    WeatherSnapshot,
    WeatherTask,
)
from .services import WeatherServiceError, get_weather, normalize_city, public_weather_payload


def _json_success(payload=None, status=200):
    data = payload or {}
    data.setdefault("success", True)
    return JsonResponse(data, status=status)


def _json_error(message, status=400):
    return JsonResponse({"success": False, "error": message}, status=status)


def register(request):
    if request.user.is_authenticated:
        return redirect("game:index")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect("game:index")
    else:
        form = RegistrationForm()

    return render(request, "registration/register.html", {"form": form})


@login_required
def index(request):
    return render(
        request,
        "game/index.html",
        {
            "game_config": config.as_public_config(),
        },
    )


def _player_state(user) -> PlayerState:
    state, _ = PlayerState.objects.get_or_create(user=user)
    return state


def _trim_history(user) -> None:
    ids = (
        CitySearchHistory.objects.filter(user=user)
        .order_by("-searched_at")
        .values_list("id", flat=True)[config.MAX_HISTORY_ENTRIES :]
    )
    if ids:
        CitySearchHistory.objects.filter(id__in=list(ids)).delete()


def _serialize_task(task: WeatherTask) -> dict:
    return {
        "id": task.id,
        "city": task.city,
        "title": task.title,
        "notes": task.notes,
        "status": task.status,
        "status_label": task.get_status_display(),
        "created_at": timezone.localtime(task.created_at).isoformat(),
        "updated_at": timezone.localtime(task.updated_at).isoformat(),
    }


@login_required
@require_GET
def api_game_state(request):
    state = _player_state(request.user)
    upgrades = list(request.user.upgrades.values_list("upgrade_key", flat=True))
    return _json_success(
        {
            "data": {
                "currentFloor": state.current_floor,
                "coins": state.coins,
                "totalFloorsTravelled": state.total_floors_travelled,
                "floorBuffer": config.FLOOR_BUFFER,
                "weatherLookupPrice": config.WEATHER_LOOKUP_PRICE,
                "upgrades": upgrades,
            }
        }
    )


@login_required
@require_POST
def api_game_progress(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _json_error("Некорректные данные")

    target_floor = payload.get("current_floor")
    floors_travelled = payload.get("floors_travelled", 0)

    try:
        target_floor = int(target_floor)
        floors_travelled = int(floors_travelled)
    except (TypeError, ValueError):
        return _json_error("Переданы неверные значения")

    if floors_travelled < 0:
        return _json_error("Количество этажей не может быть отрицательным")

    state = _player_state(request.user)
    delta = abs(target_floor - state.current_floor)
    floors_travelled = max(floors_travelled, delta)

    if floors_travelled > config.MAX_FLOOR_TRAVEL_BURST:
        return _json_error("Слишком большой скачок этажей")

    coins_earned = floors_travelled * config.COINS_PER_FLOOR

    state.current_floor = target_floor
    state.coins += coins_earned
    state.total_floors_travelled += floors_travelled
    state.save(update_fields=["current_floor", "coins", "total_floors_travelled", "updated_at"])

    return _json_success({"data": {"coins": state.coins}})


@login_required
@require_POST
def api_weather_lookup(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _json_error("Некорректные данные")

    raw_city = payload.get("city", "")
    city = normalize_city(raw_city)
    if not city:
        return _json_error("Укажите город")

    state = _player_state(request.user)
    if state.coins < config.WEATHER_LOOKUP_PRICE:
        return _json_error("Недостаточно монет")

    try:
        weather_payload = get_weather(city)
    except WeatherServiceError as exc:
        return _json_error(str(exc))

    snapshot = WeatherSnapshot.objects.filter(city__iexact=city).first()
    fetched_at = snapshot.fetched_at if snapshot else timezone.now()

    state.coins -= config.WEATHER_LOOKUP_PRICE
    state.last_weather_city = city
    state.save(update_fields=["coins", "last_weather_city", "updated_at"])

    CitySearchHistory.objects.create(user=request.user, city=city)
    _trim_history(request.user)

    return _json_success(
        {
            "data": {
                "coins": state.coins,
                "weather": public_weather_payload(city, weather_payload, fetched_at),
            }
        }
    )


@login_required
@require_GET
def api_weather_history(request):
    history = [
        {
            "city": entry.city,
            "searched_at": timezone.localtime(entry.searched_at).isoformat(),
        }
        for entry in CitySearchHistory.objects.filter(user=request.user)[: config.MAX_HISTORY_ENTRIES]
    ]
    return _json_success({"data": {"history": history}})


@login_required
@require_http_methods(["GET", "POST"])
def api_tasks(request):
    if request.method == "GET":
        city = request.GET.get("city")
        tasks = WeatherTask.objects.filter(user=request.user)
        if city:
            tasks = tasks.filter(city__iexact=normalize_city(city))
        serialized = [_serialize_task(task) for task in tasks]
        return _json_success({"data": {"tasks": serialized}})

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _json_error("Некорректные данные")

    city = normalize_city(payload.get("city", ""))
    title = (payload.get("title") or "").strip()
    notes = (payload.get("notes") or "").strip()

    if not city:
        return _json_error("Укажите город")
    if not title:
        return _json_error("Название задачи обязательно")

    task = WeatherTask.objects.create(
        user=request.user,
        city=city,
        title=title,
        notes=notes,
    )

    return _json_success({"data": {"task": _serialize_task(task)}})


@login_required
@require_http_methods(["PATCH", "DELETE"])
def api_task_detail(request, task_id: int):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)

    if request.method == "DELETE":
        task.delete()
        return _json_success()

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return _json_error("Некорректные данные")

    title = payload.get("title")
    notes = payload.get("notes")
    status = payload.get("status")

    updated_fields = []

    if title is not None:
        task.title = title.strip()
        updated_fields.append("title")

    if notes is not None:
        task.notes = notes.strip()
        updated_fields.append("notes")

    if status is not None:
        if status not in TaskStatus.values:
            return _json_error("Некорректный статус задачи")
        task.status = status
        updated_fields.append("status")

    if updated_fields:
        updated_fields.append("updated_at")
        task.save(update_fields=updated_fields)

    return _json_success({"data": {"task": _serialize_task(task)}})
