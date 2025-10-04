from __future__ import annotations

import json
import math

from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.utils import timezone

from . import config
from .forms import EmailLoginForm, RegistrationForm
from .models import (
    CitySearchHistory,
    PlayerState,
    PlayerUpgrade,
    TaskStatus,
    WeatherSnapshot,
    WeatherTask,
)
from .services import WeatherServiceError, get_weather, normalize_city, public_weather_payload


TASK_TITLE_MAX_LENGTH = WeatherTask._meta.get_field("title").max_length
TASK_NOTES_MAX_LENGTH = 2000


def _json_success(payload=None, status=200):
    data = payload or {}
    data.setdefault("success", True)
    return JsonResponse(data, status=status)


def _json_error(message, status=400):
    return JsonResponse({"success": False, "error": message}, status=status)


def _load_request_json(request):
    try:
        return json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Некорректные данные") from exc


def _clamp_coin_balance(value: int) -> int:
    return max(0, min(value, config.MAX_COIN_BALANCE))


def _clean_task_fields(title: str | None, notes: str | None) -> tuple[str, str]:
    normalized_title = (title or "").strip()
    normalized_notes = (notes or "").strip()
    if not normalized_title:
        raise ValueError("Название задачи обязательно")
    if len(normalized_title) > TASK_TITLE_MAX_LENGTH:
        raise ValueError("Слишком длинное название задачи")
    if normalized_notes and len(normalized_notes) > TASK_NOTES_MAX_LENGTH:
        normalized_notes = normalized_notes[:TASK_NOTES_MAX_LENGTH]
    return normalized_title, normalized_notes


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect("game:index")

    if request.method == "POST":
        form = EmailLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if not hasattr(user, "backend"):
                backends = getattr(settings, "AUTHENTICATION_BACKENDS", [])
                backend = backends[0] if backends else "django.contrib.auth.backends.ModelBackend"
                user.backend = backend
            login(request, user)
            return redirect("game:index")
    else:
        form = EmailLoginForm()

    return render(request, "registration/login.html", {"form": form})


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


def _player_state(user, *, for_update: bool = False) -> PlayerState:
    if for_update:
        return PlayerState.objects.select_for_update().get(user=user)
    state, _ = PlayerState.objects.get_or_create(user=user)
    return state


def _upgrade_levels(user, *, for_update: bool = False) -> dict[str, int]:
    queryset = PlayerUpgrade.objects.filter(user=user)
    if for_update:
        queryset = queryset.select_for_update()
    return {entry.upgrade_key: entry.level for entry in queryset}


def _serialize_upgrades(levels: dict[str, int]) -> list[dict]:
    serialized = []
    for definition in config.UPGRADE_CATALOG.values():
        level = levels.get(definition.key, 0)
        max_level = definition.max_level
        next_cost = None
        if max_level is None or level < max_level:
            next_cost = config.next_level_cost(definition.key, level)
        serialized.append(
            {
                "key": definition.key,
                "name": definition.name,
                "description": definition.description,
                "level": level,
                "maxLevel": max_level,
                "nextCost": next_cost,
                "metadata": definition.metadata,
            }
        )
    return serialized


def _task_limit(levels: dict[str, int]) -> int:
    return config.task_slots(levels.get("task_slot", 0))


def _weather_price(levels: dict[str, int]) -> int:
    level = levels.get("weather_radar", 0)
    return config.weather_lookup_cost(level)


def _coin_multiplier(levels: dict[str, int]) -> float:
    return config.coin_bonus_multiplier(levels.get("coin_collector", 0))


def _effects_payload(levels: dict[str, int]) -> dict:
    superlift = config.superlift_effect(levels.get("superlift", 0))
    return {
        "superlift": superlift,
        "taskLimit": _task_limit(levels),
    }


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
    levels = _upgrade_levels(request.user)
    return _json_success(
        {
            "data": {
                "currentFloor": state.current_floor,
                "coins": state.coins,
                "totalFloorsTravelled": state.total_floors_travelled,
                "floorBuffer": config.FLOOR_BUFFER,
                "weatherLookupPrice": _weather_price(levels),
                "upgrades": _serialize_upgrades(levels),
                "effects": _effects_payload(levels),
            }
        }
    )


@login_required
@require_POST
def api_game_progress(request):
    try:
        payload = _load_request_json(request)
    except ValueError as exc:
        return _json_error(str(exc))

    target_floor = payload.get("current_floor")
    floors_travelled = payload.get("floors_travelled", 0)

    try:
        target_floor = int(target_floor)
        floors_travelled = int(floors_travelled)
    except (TypeError, ValueError):
        return _json_error("Переданы неверные значения")

    if floors_travelled < 0:
        return _json_error("Количество этажей не может быть отрицательным")

    if abs(target_floor) > config.MAX_FLOOR_ABSOLUTE:
        return _json_error("Этаж вне допустимого диапазона")

    if floors_travelled > config.MAX_FLOOR_TRAVEL_BURST:
        return _json_error("Слишком большой скачок этажей")

    _player_state(request.user)  # ensure exists

    with transaction.atomic():
        state = _player_state(request.user, for_update=True)
        levels = _upgrade_levels(request.user)

        delta = abs(target_floor - state.current_floor)
        effective_travel = max(floors_travelled, delta)
        if effective_travel > config.MAX_FLOOR_TRAVEL_BURST:
            return _json_error("Слишком большой скачок этажей")

        base_coins = effective_travel * config.COINS_PER_FLOOR
        coins_earned = math.floor(base_coins * _coin_multiplier(levels))

        state.current_floor = target_floor
        state.coins = _clamp_coin_balance(state.coins + coins_earned)
        state.total_floors_travelled += effective_travel
        state.save(update_fields=["current_floor", "coins", "total_floors_travelled", "updated_at"])

    return _json_success({"data": {"coins": state.coins}})


@login_required
@require_POST
def api_weather_lookup(request):
    try:
        payload = _load_request_json(request)
    except ValueError as exc:
        return _json_error(str(exc))

    raw_city = payload.get("city", "")
    city = normalize_city(raw_city)
    if not city:
        return _json_error("Укажите город")

    state_snapshot = _player_state(request.user)
    levels_snapshot = _upgrade_levels(request.user)
    price_snapshot = _weather_price(levels_snapshot)

    if state_snapshot.coins < price_snapshot:
        return _json_error("Недостаточно монет")

    try:
        weather_payload = get_weather(city)
    except WeatherServiceError as exc:
        return _json_error(str(exc))

    snapshot = WeatherSnapshot.objects.filter(city__iexact=city).first()
    fetched_at = snapshot.fetched_at if snapshot else timezone.now()

    with transaction.atomic():
        state = _player_state(request.user, for_update=True)
        levels = _upgrade_levels(request.user)
        price = _weather_price(levels)
        if state.coins < price:
            return _json_error("Недостаточно монет")

        state.coins = _clamp_coin_balance(state.coins - price)
        state.last_weather_city = city
        state.save(update_fields=["coins", "last_weather_city", "updated_at"])

        CitySearchHistory.objects.create(user=request.user, city=city)
        _trim_history(request.user)

    response_effects = _effects_payload(levels)

    return _json_success(
        {
            "data": {
                "coins": state.coins,
                "weather": public_weather_payload(city, weather_payload, fetched_at),
                "weatherPrice": price,
                "effects": response_effects,
            }
        }
    )


@login_required
@require_POST
def api_game_reset(request):
    with transaction.atomic():
        PlayerUpgrade.objects.filter(user=request.user).delete()
        WeatherTask.objects.filter(user=request.user).delete()
        CitySearchHistory.objects.filter(user=request.user).delete()
        PlayerState.objects.filter(user=request.user).delete()
        state = PlayerState.objects.create(user=request.user)

    levels: dict[str, int] = {}
    return _json_success(
        {
            "data": {
                "currentFloor": state.current_floor,
                "coins": state.coins,
                "totalFloorsTravelled": state.total_floors_travelled,
                "weatherPrice": _weather_price(levels),
                "upgrades": _serialize_upgrades(levels),
                "effects": _effects_payload(levels),
                "taskLimit": _task_limit(levels),
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
        levels = _upgrade_levels(request.user)
        limit = _task_limit(levels)
        tasks = WeatherTask.objects.filter(user=request.user)
        if city:
            tasks = tasks.filter(city__iexact=normalize_city(city))
        serialized = [_serialize_task(task) for task in tasks]
        return _json_success({"data": {"tasks": serialized, "limit": limit}})

    try:
        payload = _load_request_json(request)
    except ValueError as exc:
        return _json_error(str(exc))

    city = normalize_city(payload.get("city", ""))
    if not city:
        return _json_error("Укажите город")

    try:
        title, notes = _clean_task_fields(payload.get("title"), payload.get("notes"))
    except ValueError as exc:
        return _json_error(str(exc))

    with transaction.atomic():
        levels = _upgrade_levels(request.user)
        limit = _task_limit(levels)

        if limit <= 0:
            return _json_error("Купите улучшение 'Органайзер задач', чтобы добавлять задачи")

        city_tasks = WeatherTask.objects.filter(user=request.user, city__iexact=city)
        if city_tasks.filter(title__iexact=title).exists():
            return _json_error("Такая задача уже существует для этого города")

        if city_tasks.count() >= limit:
            return _json_error("Достигнут лимит задач для этого города")

        task = WeatherTask.objects.create(
            user=request.user,
            city=city,
            title=title,
            notes=notes,
        )

    return _json_success({"data": {"task": _serialize_task(task), "limit": limit}})


@login_required
@require_http_methods(["GET", "POST"])
def api_upgrades(request):
    _player_state(request.user)  # ensure exists
    state = _player_state(request.user)
    levels = _upgrade_levels(request.user)

    if request.method == "GET":
        return _json_success(
            {
                "data": {
                    "coins": state.coins,
                    "upgrades": _serialize_upgrades(levels),
                    "weatherPrice": _weather_price(levels),
                    "effects": _effects_payload(levels),
                }
            }
        )

    try:
        payload = _load_request_json(request)
    except ValueError as exc:
        return _json_error(str(exc))

    key = payload.get("key")
    if not key:
        return _json_error("Не указано улучшение")

    try:
        definition = config.get_upgrade_definition(key)
    except KeyError as exc:
        return _json_error(str(exc))

    current_level = levels.get(key, 0)
    if definition.max_level is not None and current_level >= definition.max_level:
        return _json_error("Уже достигнут максимальный уровень")

    cost = config.next_level_cost(key, current_level)

    with transaction.atomic():
        state = PlayerState.objects.select_for_update().get(user=request.user)
        if state.coins < cost:
            return _json_error("Недостаточно монет")

        upgrade = (
            PlayerUpgrade.objects.select_for_update()
            .filter(user=request.user, upgrade_key=key)
            .first()
        )

        if upgrade is None:
            upgrade = PlayerUpgrade(user=request.user, upgrade_key=key, level=1)
        else:
            upgrade.level += 1

        upgrade.save()
        state.coins = _clamp_coin_balance(state.coins - cost)
        state.save(update_fields=["coins", "updated_at"])

    levels = _upgrade_levels(request.user)

    return _json_success(
        {
            "data": {
                "coins": state.coins,
                "upgrades": _serialize_upgrades(levels),
                "weatherPrice": _weather_price(levels),
                "effects": _effects_payload(levels),
            }
        }
    )


@login_required
@require_http_methods(["PATCH", "DELETE"])
def api_task_detail(request, task_id: int):
    task = get_object_or_404(WeatherTask, id=task_id, user=request.user)

    if request.method == "DELETE":
        task.delete()
        return _json_success()

    try:
        payload = _load_request_json(request)
    except ValueError as exc:
        return _json_error(str(exc))

    title = payload.get("title")
    notes = payload.get("notes")
    status = payload.get("status")

    updated_fields = []

    if title is not None:
        cleaned_title = (title or "").strip()
        if not cleaned_title:
            return _json_error("Название задачи обязательно")
        if len(cleaned_title) > TASK_TITLE_MAX_LENGTH:
            return _json_error("Слишком длинное название задачи")
        task.title = cleaned_title
        updated_fields.append("title")

    if notes is not None:
        cleaned_notes = (notes or "").strip()
        if cleaned_notes and len(cleaned_notes) > TASK_NOTES_MAX_LENGTH:
            cleaned_notes = cleaned_notes[:TASK_NOTES_MAX_LENGTH]
        task.notes = cleaned_notes
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
