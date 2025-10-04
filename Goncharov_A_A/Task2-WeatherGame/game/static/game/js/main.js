(function () {
    const configNode = document.getElementById('game-config');
    const config = configNode ? JSON.parse(configNode.textContent) : {};

    const upgradeDefinitionsList = Array.isArray(config.upgrades) ? config.upgrades : [];
    const upgradeDefinitions = upgradeDefinitionsList.reduce((acc, definition) => {
        if (definition && definition.key) {
            acc[definition.key] = definition;
        }
        return acc;
    }, {});

    const numberFormatter = new Intl.NumberFormat('ru-RU');

    const state = {
        currentFloor: 0,
        coins: 0,
        floorsTraversedBuffer: 0,
        floorWindow: config.floorBuffer ?? 50,
        weatherPrice: config.weatherLookupPrice ?? 250,
        coinsPerFloor: config.coinsPerFloor ?? 1,
        maxFloor: Number.isFinite(config.maxFloor) ? config.maxFloor : null,
        maxFloorBurst: Number.isFinite(config.maxFloorBurst) ? config.maxFloorBurst : null,
        maxCoins: Number.isFinite(config.maxCoins) ? config.maxCoins : null,
        upgradeDefinitionsList,
        upgradeDefinitions,
        upgradeData: [],
        upgradeLevels: {},
        currentCity: null,
        taskLimit: 0,
        currentTasksCount: 0,
        effects: {},
        superliftTimer: null,
    };

    const elements = {
        floorContainer: document.getElementById('floors'),
        hudFloor: document.getElementById('hud-floor'),
        hudCoins: document.getElementById('hud-coins'),
        weatherButton: document.getElementById('btn-weather'),
        upgradesButton: document.getElementById('btn-upgrades'),
        weatherModal: document.getElementById('weather-modal'),
        upgradesModal: document.getElementById('upgrades-modal'),
        weatherForm: document.getElementById('weather-form'),
        weatherCityInput: document.getElementById('weather-city'),
        weatherPrice: document.getElementById('weather-price'),
        weatherMessage: document.getElementById('weather-message'),
        weatherInfo: document.getElementById('weather-info'),
        weatherCityName: document.getElementById('weather-city-name'),
        weatherDescription: document.getElementById('weather-description'),
        weatherTemp: document.getElementById('weather-temp'),
        weatherFeels: document.getElementById('weather-feels'),
        weatherHumidity: document.getElementById('weather-humidity'),
        weatherPressure: document.getElementById('weather-pressure'),
        weatherWind: document.getElementById('weather-wind'),
        weatherIcon: document.getElementById('weather-icon'),
        weatherUpdated: document.getElementById('weather-updated'),
        tasksSection: document.getElementById('tasks'),
        tasksList: document.getElementById('task-list'),
        taskForm: document.getElementById('task-form'),
        taskTitle: document.getElementById('task-title'),
        taskNotes: document.getElementById('task-notes'),
        taskToggle: document.getElementById('task-add-toggle'),
        taskCancel: document.getElementById('task-cancel'),
        taskLimitLabel: document.getElementById('task-limit'),
        historySection: document.getElementById('history'),
        historyList: document.getElementById('history-list'),
        upgradesContent: document.getElementById('upgrades-content'),
        hudEffects: document.getElementById('hud-effects'),
        hudEffectsLabel: document.getElementById('hud-effects-label'),
        toastRoot: document.getElementById('toast-root'),
    };

    if (!elements.floorContainer) {
        return;
    }

    let syncTimer = null;
    let ignoreScroll = false;
    let floorBase = state.currentFloor - state.floorWindow;

    const TASK_LABELS = {
        pending: 'В ожидании',
        in_progress: 'В работе',
        done: 'Выполнена',
    };

    const TOAST_TIMEOUT = 4500;

    function formatNumber(value) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        return numberFormatter.format(value);
    }

    function clampFloor(value) {
        if (!Number.isFinite(value) || state.maxFloor === null) {
            return value;
        }
        const limit = state.maxFloor;
        return Math.max(-limit, Math.min(limit, value));
    }

    function clampCoins(value) {
        if (!Number.isFinite(value)) {
            return 0;
        }
        if (state.maxCoins === null) {
            return Math.max(0, value);
        }
        return Math.max(0, Math.min(value, state.maxCoins));
    }

    function showToast(message, type = 'info') {
        if (!elements.toastRoot || !message) {
            return;
        }
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        toast.textContent = message;
        elements.toastRoot.appendChild(toast);
        requestAnimationFrame(() => {
            toast.classList.add('is-visible');
        });
        window.setTimeout(() => {
            toast.classList.remove('is-visible');
            window.setTimeout(() => {
                toast.remove();
            }, 250);
        }, TOAST_TIMEOUT);
    }

    function setButtonBusy(button, isBusy) {
        if (!button) {
            return;
        }
        if (isBusy) {
            button.classList.add('is-busy');
            button.disabled = true;
        } else {
            button.classList.remove('is-busy');
            button.disabled = false;
        }
    }

    function getCSRFToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    async function apiRequest(url, options = {}) {
        const opts = {
            headers: {
                Accept: 'application/json',
            },
            credentials: 'same-origin',
            ...options,
        };

        if (opts.method && opts.method.toUpperCase() !== 'GET') {
            opts.headers['Content-Type'] = 'application/json';
            opts.headers['X-CSRFToken'] = getCSRFToken();
        }

        let response;
        try {
            response = await fetch(url, opts);
        } catch (networkError) {
            throw new Error('Сеть недоступна, повторите попытку позже');
        }

        const data = await response.json().catch(() => ({ success: false, error: 'Ошибка разбора ответа' }));
        if (!response.ok || data.success === false) {
            const message = data.error || data.detail || 'Произошла ошибка';
            throw new Error(message);
        }
        return data;
    }

    function setUpgradeData(upgrades) {
        state.upgradeData = Array.isArray(upgrades) ? upgrades : [];
        state.upgradeLevels = {};
        state.upgradeData.forEach((item) => {
            if (item && item.key) {
                state.upgradeLevels[item.key] = item.level ?? 0;
            }
        });
    }

    function updateHud() {
        elements.hudFloor.textContent = formatNumber(state.currentFloor);
        elements.hudCoins.textContent = formatNumber(state.coins);
        if (elements.weatherPrice) {
            elements.weatherPrice.textContent = formatNumber(state.weatherPrice);
        }
    }

    function buildFloorElement(number) {
        const floor = document.createElement('div');
        floor.className = 'floor';
        floor.dataset.floorNumber = String(number);

        const label = document.createElement('div');
        label.className = 'floor__number';
        label.textContent = number;

        floor.appendChild(label);
        return floor;
    }

    function recenterFloors(centerFloor) {
        const clampedCenter = clampFloor(centerFloor);
        if (clampedCenter !== centerFloor) {
            state.currentFloor = clampedCenter;
        }
        floorBase = clampedCenter - state.floorWindow;
        elements.floorContainer.innerHTML = '';
        for (let offset = 0; offset <= state.floorWindow * 2; offset += 1) {
            const floorNumber = floorBase + offset;
            elements.floorContainer.appendChild(buildFloorElement(floorNumber));
        }

        const targetScroll = state.floorWindow * elements.floorContainer.clientHeight;
        ignoreScroll = true;
        requestAnimationFrame(() => {
            elements.floorContainer.scrollTop = targetScroll;
            requestAnimationFrame(() => {
                ignoreScroll = false;
            });
        });
    }

    function incrementFloors(delta) {
        if (!Number.isFinite(delta) || delta <= 0) {
            return;
        }
        const target = clampFloor(state.currentFloor + delta);
        const applied = target - state.currentFloor;
        if (applied <= 0) {
            return;
        }
        state.currentFloor = target;
        state.floorsTraversedBuffer += applied;
        updateHud();
        recenterFloors(state.currentFloor);
        scheduleSync();
    }

    function scheduleSync() {
        if (syncTimer || state.floorsTraversedBuffer === 0) {
            return;
        }
        syncTimer = window.setTimeout(async () => {
            syncTimer = null;
            if (state.floorsTraversedBuffer === 0) {
                return;
            }
            const payload = {
                current_floor: state.currentFloor,
                floors_travelled: state.floorsTraversedBuffer,
            };
            try {
                const response = await apiRequest('/api/game/progress/', {
                    method: 'POST',
                    body: JSON.stringify(payload),
                });
                state.coins = clampCoins(response.data.coins);
                state.floorsTraversedBuffer = 0;
                updateHud();
            } catch (error) {
                showToast(error.message, 'error');
            } finally {
                if (state.floorsTraversedBuffer > 0) {
                    scheduleSync();
                }
            }
        }, 600);
    }

    function handleScroll() {
        if (ignoreScroll) {
            return;
        }
        const height = elements.floorContainer.clientHeight;
        if (!height) {
            return;
        }
        const index = Math.round(elements.floorContainer.scrollTop / height);
        const floorNumber = floorBase + index;
        const clamped = clampFloor(floorNumber);
        if (clamped !== floorNumber) {
            showToast('Достигнут предел этажа', 'info');
            recenterFloors(state.currentFloor);
            return;
        }

        if (clamped === state.currentFloor) {
            return;
        }

        const travelled = Math.abs(clamped - state.currentFloor);
        if (state.maxFloorBurst && travelled > state.maxFloorBurst) {
            showToast(`Нельзя перемещаться более чем на ${state.maxFloorBurst} этажей за раз`, 'error');
            recenterFloors(state.currentFloor);
            return;
        }

        state.currentFloor = clamped;
        state.floorsTraversedBuffer += travelled;
        updateHud();

        if (index < 10 || index > state.floorWindow * 2 - 10) {
            recenterFloors(state.currentFloor);
        }

        scheduleSync();
    }

    function setupSuperlift(effect) {
        if (state.superliftTimer) {
            window.clearInterval(state.superliftTimer);
            state.superliftTimer = null;
        }
        if (!effect || !effect.floors || effect.floors <= 0) {
            return;
        }
        const interval = Math.max(effect.interval_ms || 5000, 500);
        state.superliftTimer = window.setInterval(() => {
            incrementFloors(effect.floors);
        }, interval);
    }

    function updateEffectsDisplay() {
        if (!elements.hudEffects || !elements.hudEffectsLabel) {
            return;
        }
        const effect = state.effects?.superlift;
        if (effect && effect.floors > 0) {
            const seconds = Math.max(1, Math.round((effect.interval_ms || 1000) / 1000));
            elements.hudEffectsLabel.textContent = `Суперлифты: +${effect.floors} этаж(а) каждые ${seconds} с`;
            elements.hudEffects.removeAttribute('data-hidden');
        } else {
            elements.hudEffectsLabel.textContent = '';
            elements.hudEffects.setAttribute('data-hidden', 'true');
        }
    }

    function updateTaskControls() {
        if (!elements.taskToggle) {
            return;
        }
        const limit = state.taskLimit ?? 0;
        const remaining = limit - state.currentTasksCount;
        if (elements.taskLimitLabel) {
            if (limit > 0) {
                elements.taskLimitLabel.textContent = `${state.currentTasksCount}/${limit}`;
                elements.taskLimitLabel.removeAttribute('data-hidden');
            } else if (limit === 0) {
                elements.taskLimitLabel.textContent = 'Нет доступных слотов';
                elements.taskLimitLabel.removeAttribute('data-hidden');
            } else {
                elements.taskLimitLabel.setAttribute('data-hidden', 'true');
            }
        }
        if (limit <= 0) {
            elements.taskToggle.disabled = true;
            elements.taskToggle.textContent = 'Нет слотов задач';
            elements.taskForm?.setAttribute('data-hidden', 'true');
        } else if (remaining <= 0) {
            elements.taskToggle.disabled = true;
            elements.taskToggle.textContent = 'Лимит задач заполнен';
            elements.taskForm?.setAttribute('data-hidden', 'true');
        } else {
            elements.taskToggle.disabled = false;
            elements.taskToggle.textContent = 'Новая задача';
        }
    }

    function applyUpgradeEffects(effects) {
        state.effects = effects || {};
        state.taskLimit = state.effects.taskLimit ?? 0;
        setupSuperlift(state.effects.superlift);
        updateTaskControls();
        updateEffectsDisplay();
    }

    function renderWeather(data) {
        elements.weatherInfo.removeAttribute('data-hidden');
        elements.weatherCityName.textContent = data.city;
        elements.weatherDescription.textContent = data.description || '';
        elements.weatherTemp.textContent = data.temperature ?? '—';
        elements.weatherFeels.textContent = data.feels_like ?? '—';
        elements.weatherHumidity.textContent = data.humidity ?? '—';
        elements.weatherPressure.textContent = data.pressure ?? '—';
        elements.weatherWind.textContent = data.wind_speed ?? '—';
        if (elements.weatherUpdated) {
            if (data.fetched_at) {
                const updatedAt = new Date(data.fetched_at);
                elements.weatherUpdated.textContent = updatedAt.toLocaleString();
            } else {
                elements.weatherUpdated.textContent = '—';
            }
        }
        if (data.icon) {
            elements.weatherIcon.src = `https://openweathermap.org/img/wn/${data.icon}@2x.png`;
            elements.weatherIcon.style.display = '';
        } else {
            elements.weatherIcon.src = '';
            elements.weatherIcon.style.display = 'none';
        }
    }

    function renderTasks(tasks) {
        elements.tasksList.innerHTML = '';
        state.currentTasksCount = tasks.length;
        if (!tasks.length) {
            const empty = document.createElement('li');
            empty.textContent = 'Нет задач для этого города.';
            empty.className = 'tasks__empty';
            elements.tasksList.appendChild(empty);
            updateTaskControls();
            return;
        }

        tasks.forEach((task) => {
            const item = document.createElement('li');
            item.className = 'task-item';
            item.dataset.id = task.id;

            const header = document.createElement('div');
            header.className = 'task-item__header';

            const title = document.createElement('h4');
            title.className = 'task-item__title';
            title.textContent = task.title;

            const actions = document.createElement('div');
            actions.className = 'task-item__actions';

            const statusSelect = document.createElement('select');
            Object.entries(TASK_LABELS).forEach(([value, label]) => {
                const option = document.createElement('option');
                option.value = value;
                option.textContent = label;
                if (task.status === value) {
                    option.selected = true;
                }
                statusSelect.appendChild(option);
            });
            statusSelect.addEventListener('change', async () => {
                try {
                    await apiRequest(`/api/tasks/${task.id}/`, {
                        method: 'PATCH',
                        body: JSON.stringify({ status: statusSelect.value }),
                    });
                    task.status = statusSelect.value;
                    showToast('Статус задачи обновлён', 'success');
                } catch (error) {
                    statusSelect.value = task.status;
                    showToast(error.message, 'error');
                }
            });

            const removeBtn = document.createElement('button');
            removeBtn.className = 'btn btn--ghost';
            removeBtn.type = 'button';
            removeBtn.textContent = 'Удалить';
            removeBtn.addEventListener('click', async () => {
                if (!confirm('Удалить задачу?')) {
                    return;
                }
                try {
                    await apiRequest(`/api/tasks/${task.id}/`, {
                        method: 'DELETE',
                    });
                    item.remove();
                    state.currentTasksCount = Math.max(state.currentTasksCount - 1, 0);
                    updateTaskControls();
                    showToast('Задача удалена', 'success');
                } catch (error) {
                    showToast(error.message, 'error');
                }
            });

            actions.appendChild(statusSelect);
            actions.appendChild(removeBtn);

            header.appendChild(title);
            header.appendChild(actions);

            item.appendChild(header);

            if (task.notes) {
                const notes = document.createElement('p');
                notes.className = 'task-item__notes';
                notes.textContent = task.notes;
                item.appendChild(notes);
            }

            elements.tasksList.appendChild(item);
        });

        updateTaskControls();
    }

    function renderHistory(entries) {
        elements.historyList.innerHTML = '';
        if (!entries.length) {
            const empty = document.createElement('li');
            empty.textContent = 'История пока пуста';
            elements.historyList.appendChild(empty);
            return;
        }
        entries.forEach((entry) => {
            const item = document.createElement('li');
            const time = new Date(entry.searched_at);
            const cityLabel = document.createElement('span');
            cityLabel.textContent = entry.city;
            const timeLabel = document.createElement('time');
            timeLabel.dateTime = time.toISOString();
            timeLabel.textContent = time.toLocaleString();
            item.appendChild(cityLabel);
            item.appendChild(timeLabel);
            elements.historyList.appendChild(item);
        });
    }

    function renderUpgrades() {
        if (!elements.upgradesContent) {
            return;
        }
        if (!state.upgradeDefinitionsList.length) {
            elements.upgradesContent.innerHTML = '<p>Улучшения появятся позже. Добавьте их в <code>game/config.py</code>.</p>';
            return;
        }

        const dataByKey = state.upgradeData.reduce((acc, item) => {
            if (item && item.key) {
                acc[item.key] = item;
            }
            return acc;
        }, {});

        const list = document.createElement('ul');
        list.className = 'upgrades__list';

        state.upgradeDefinitionsList.forEach((definition) => {
            const item = document.createElement('li');
            item.className = 'upgrades__item';

            const title = document.createElement('h4');
            title.textContent = definition.name;

            const description = document.createElement('p');
            description.textContent = definition.description;

            const info = dataByKey[definition.key] || {
                level: 0,
                maxLevel: definition.max_level,
                nextCost: definition.base_cost,
            };

            let progress = null;
            if (definition.max_level !== null && definition.max_level !== undefined) {
                progress = document.createElement('div');
                progress.className = 'upgrades__progress';
                const progressBar = document.createElement('div');
                progressBar.className = 'upgrades__progress-bar';
                const ratio = info.maxLevel ? Math.min((info.level ?? 0) / info.maxLevel, 1) : 0;
                progressBar.style.transform = `scaleX(${Math.max(0, ratio)})`;
                progress.appendChild(progressBar);
            }

            const footer = document.createElement('div');
            footer.className = 'upgrades__footer';

            const levelLabel = document.createElement('span');
            if (info.maxLevel === null || info.maxLevel === undefined) {
                levelLabel.textContent = `Уровень: ${info.level ?? 0}`;
            } else {
                levelLabel.textContent = `Уровень: ${info.level ?? 0}/${info.maxLevel}`;
            }

            const action = document.createElement('button');
            action.className = 'btn btn--ghost';
            action.type = 'button';

            const canUpgrade = typeof info.nextCost === 'number';
            if (!canUpgrade) {
                action.textContent = 'Максимальный уровень';
                action.disabled = true;
            } else if (state.coins >= info.nextCost) {
                action.textContent = `Купить за ${formatNumber(info.nextCost)}`;
                action.disabled = false;
                action.addEventListener('click', async () => {
                    action.disabled = true;
                    action.textContent = 'Покупка...';
                    await handleUpgradePurchase(definition.key);
                });
            } else {
                action.textContent = `Нужно ${formatNumber(info.nextCost)}`;
                action.disabled = true;
            }

            footer.appendChild(levelLabel);
            footer.appendChild(action);

            item.appendChild(title);
            item.appendChild(description);
            if (progress) {
                item.appendChild(progress);
            }
            item.appendChild(footer);
            list.appendChild(item);
        });

        elements.upgradesContent.innerHTML = '';
        elements.upgradesContent.appendChild(list);
    }

    async function fetchUpgrades() {
        if (elements.upgradesContent) {
            elements.upgradesContent.innerHTML = '<p>Загрузка улучшений...</p>';
        }
        try {
            const response = await apiRequest('/api/upgrades/');
            state.coins = clampCoins(response.data.coins);
            if (typeof response.data.weatherPrice === 'number') {
                state.weatherPrice = response.data.weatherPrice;
            }
            setUpgradeData(response.data.upgrades);
            applyUpgradeEffects(response.data.effects);
            updateHud();
            renderUpgrades();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function handleUpgradePurchase(key) {
        if (!key) {
            return;
        }
        try {
            const response = await apiRequest('/api/upgrades/', {
                method: 'POST',
                body: JSON.stringify({ key }),
            });
            state.coins = clampCoins(response.data.coins);
            if (typeof response.data.weatherPrice === 'number') {
                state.weatherPrice = response.data.weatherPrice;
            }
            setUpgradeData(response.data.upgrades);
            applyUpgradeEffects(response.data.effects);
            updateHud();
            renderUpgrades();
            if (state.currentCity) {
                await loadTasks(state.currentCity);
            }
            showToast('Улучшение приобретено', 'success');
        } catch (error) {
            showToast(error.message, 'error');
            renderUpgrades();
        }
    }

    async function loadGameState() {
        try {
            const response = await apiRequest('/api/game/state/');
            state.currentFloor = response.data.currentFloor;
            state.coins = clampCoins(response.data.coins);
            state.weatherPrice = response.data.weatherLookupPrice;
            state.floorWindow = response.data.floorBuffer;
            setUpgradeData(response.data.upgrades);
            applyUpgradeEffects(response.data.effects);
            recenterFloors(state.currentFloor);
            updateHud();
            renderUpgrades();
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function loadTasks(city) {
        if (!city) {
            return;
        }
        try {
            const response = await apiRequest(`/api/tasks/?city=${encodeURIComponent(city)}`);
            state.taskLimit = response.data.limit ?? state.taskLimit;
            elements.tasksSection.removeAttribute('data-hidden');
            renderTasks(response.data.tasks);
        } catch (error) {
            showToast(error.message, 'error');
            elements.tasksSection.setAttribute('data-hidden', 'true');
            state.currentTasksCount = 0;
            updateTaskControls();
        }
    }

    async function loadHistory() {
        try {
            const response = await apiRequest('/api/weather/history/');
            if (response.data.history.length) {
                elements.historySection.removeAttribute('data-hidden');
                renderHistory(response.data.history);
            } else {
                elements.historySection.setAttribute('data-hidden', 'true');
            }
        } catch (error) {
            showToast(error.message, 'error');
        }
    }

    async function handleWeatherSubmit(event) {
        event.preventDefault();
        const city = elements.weatherCityInput.value.trim();
        if (!city) {
            elements.weatherMessage.textContent = 'Введите название города';
            return;
        }
        if (state.coins < state.weatherPrice) {
            elements.weatherMessage.textContent = 'Недостаточно монет';
            return;
        }

        elements.weatherMessage.textContent = '';
        elements.weatherForm.classList.add('is-loading');
        const submitButton = elements.weatherForm.querySelector('[type="submit"]');
        setButtonBusy(submitButton, true);
        elements.weatherCityInput.disabled = true;
        try {
            const response = await apiRequest('/api/weather/lookup/', {
                method: 'POST',
                body: JSON.stringify({ city }),
            });
            state.coins = clampCoins(response.data.coins);
            if (typeof response.data.weatherPrice === 'number') {
                state.weatherPrice = response.data.weatherPrice;
            }
            if (response.data.effects) {
                applyUpgradeEffects(response.data.effects);
            }
            state.currentCity = response.data.weather.city;
            elements.weatherCityInput.value = state.currentCity;
            updateHud();
            renderWeather(response.data.weather);
            elements.tasksSection.removeAttribute('data-hidden');
            elements.historySection.removeAttribute('data-hidden');
            await loadTasks(state.currentCity);
            await loadHistory();
            elements.weatherMessage.textContent = '';
            showToast('Погода обновлена', 'success');
        } catch (error) {
            elements.weatherMessage.textContent = error.message;
            showToast(error.message, 'error');
        } finally {
            elements.weatherForm.classList.remove('is-loading');
            elements.weatherCityInput.disabled = false;
            setButtonBusy(submitButton, false);
        }
    }

    async function handleTaskSubmit(event) {
        event.preventDefault();
        const city = state.currentCity;
        if (!city) {
            showToast('Сначала получите погоду города.', 'info');
            return;
        }
        if (state.taskLimit > 0 && state.currentTasksCount >= state.taskLimit) {
            showToast('Достигнут лимит задач для этого города.', 'error');
            return;
        }
        const title = elements.taskTitle.value.trim();
        const notes = elements.taskNotes.value.trim();
        if (!title) {
            showToast('Введите название задачи.', 'error');
            return;
        }
        const submitButton = elements.taskForm.querySelector('[type="submit"]');
        setButtonBusy(submitButton, true);
        try {
            const response = await apiRequest('/api/tasks/', {
                method: 'POST',
                body: JSON.stringify({ city, title, notes }),
            });
            state.taskLimit = response.data.limit ?? state.taskLimit;
            elements.taskTitle.value = '';
            elements.taskNotes.value = '';
            elements.taskForm.setAttribute('data-hidden', 'true');
            await loadTasks(city);
            showToast('Задача добавлена', 'success');
        } catch (error) {
            showToast(error.message, 'error');
        }
        setButtonBusy(submitButton, false);
    }

    function setupTaskForm() {
        elements.taskForm?.addEventListener('submit', handleTaskSubmit);
        elements.taskCancel?.addEventListener('click', () => {
            elements.taskForm.setAttribute('data-hidden', 'true');
        });
        elements.taskToggle?.addEventListener('click', () => {
            if (elements.taskToggle.disabled) {
                return;
            }
            const hidden = elements.taskForm.hasAttribute('data-hidden');
            if (hidden) {
                elements.taskForm.removeAttribute('data-hidden');
                elements.taskTitle.focus();
            } else {
                elements.taskForm.setAttribute('data-hidden', 'true');
            }
        });
    }

    function setupModals() {
        elements.weatherButton?.addEventListener('click', () => {
            openModal(elements.weatherModal);
        });
        elements.upgradesButton?.addEventListener('click', () => {
            openModal(elements.upgradesModal);
            fetchUpgrades();
        });

        document.querySelectorAll('.modal__close').forEach((btn) => {
            btn.addEventListener('click', () => {
                const modal = btn.closest('.modal');
                closeModal(modal);
            });
        });

        document.querySelectorAll('.modal').forEach((modal) => {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    closeModal(modal);
                }
            });
        });
    }

    function openModal(modal) {
        modal?.removeAttribute('data-hidden');
    }

    function closeModal(modal) {
        modal?.setAttribute('data-hidden', 'true');
    }

    function setupWeatherForm() {
        elements.weatherForm?.addEventListener('submit', handleWeatherSubmit);
        if (elements.weatherPrice) {
            elements.weatherPrice.textContent = state.weatherPrice;
        }
    }

    function setupFloors() {
        recenterFloors(state.currentFloor);
        elements.floorContainer.addEventListener('scroll', handleScroll);
        window.addEventListener('resize', () => recenterFloors(state.currentFloor));
    }

    async function init() {
        setupFloors();
        setupModals();
        setupWeatherForm();
        setupTaskForm();
        await loadGameState();
        await loadHistory();
    }

    document.addEventListener('DOMContentLoaded', init);
})();
