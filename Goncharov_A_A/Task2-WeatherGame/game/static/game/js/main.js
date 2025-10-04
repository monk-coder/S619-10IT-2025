(function () {
    const configNode = document.getElementById('game-config');
    const config = configNode ? JSON.parse(configNode.textContent) : {};

    const state = {
        currentFloor: 0,
        coins: 0,
        floorsTraversedBuffer: 0,
        floorWindow: config.floorBuffer ?? 50,
        weatherPrice: config.weatherLookupPrice ?? 250,
        coinsPerFloor: config.coinsPerFloor ?? 1,
        upgradeDefinitions: config.upgrades ?? [],
        upgrades: [],
        currentCity: null,
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
        tasksSection: document.getElementById('tasks'),
        tasksList: document.getElementById('task-list'),
        taskForm: document.getElementById('task-form'),
        taskTitle: document.getElementById('task-title'),
        taskNotes: document.getElementById('task-notes'),
        taskToggle: document.getElementById('task-add-toggle'),
        taskCancel: document.getElementById('task-cancel'),
        historySection: document.getElementById('history'),
        historyList: document.getElementById('history-list'),
        upgradesContent: document.getElementById('upgrades-content'),
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

    function getCSRFToken() {
        const match = document.cookie.match(/csrftoken=([^;]+)/);
        return match ? decodeURIComponent(match[1]) : '';
    }

    async function apiRequest(url, options = {}) {
        const opts = {
            headers: {
                'Accept': 'application/json',
            },
            ...options,
        };

        if (opts.method && opts.method.toUpperCase() !== 'GET') {
            opts.headers['Content-Type'] = 'application/json';
            opts.headers['X-CSRFToken'] = getCSRFToken();
        }

        const response = await fetch(url, opts);
        const data = await response.json().catch(() => ({ success: false, error: 'Ошибка разбора ответа' }));
        if (!response.ok || data.success === false) {
            const message = data.error || data.detail || 'Произошла ошибка';
            throw new Error(message);
        }
        return data;
    }

    function updateHud() {
        elements.hudFloor.textContent = state.currentFloor;
        elements.hudCoins.textContent = state.coins;
        elements.weatherPrice.textContent = state.weatherPrice;
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
        floorBase = centerFloor - state.floorWindow;
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
                state.coins = response.data.coins;
                state.floorsTraversedBuffer = 0;
                updateHud();
            } catch (error) {
                console.error(error);
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
        if (floorNumber === state.currentFloor) {
            return;
        }

        const travelled = Math.abs(floorNumber - state.currentFloor);
        state.currentFloor = floorNumber;
        state.floorsTraversedBuffer += travelled;
        updateHud();

        if (index < 10 || index > (state.floorWindow * 2) - 10) {
            recenterFloors(state.currentFloor);
        }

        scheduleSync();
    }

    async function loadGameState() {
        try {
            const response = await apiRequest('/api/game/state/');
            state.currentFloor = response.data.currentFloor;
            state.coins = response.data.coins;
            state.upgrades = response.data.upgrades;
            state.weatherPrice = response.data.weatherLookupPrice;
            state.floorWindow = response.data.floorBuffer;
            recenterFloors(state.currentFloor);
            updateHud();
            renderUpgrades();
        } catch (error) {
            console.error(error);
        }
    }

    function openModal(modal) {
        modal?.removeAttribute('data-hidden');
    }

    function closeModal(modal) {
        modal?.setAttribute('data-hidden', 'true');
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
        if (!tasks.length) {
            const empty = document.createElement('li');
            empty.textContent = 'Нет задач для этого города.';
            empty.className = 'tasks__empty';
            elements.tasksList.appendChild(empty);
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
                } catch (error) {
                    statusSelect.value = task.status;
                    alert(error.message);
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
                } catch (error) {
                    alert(error.message);
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
    }

    function renderHistory(entries) {
        elements.historyList.innerHTML = '';
        entries.forEach((entry) => {
            const item = document.createElement('li');
            const time = new Date(entry.searched_at);
            item.textContent = `${entry.city} — ${time.toLocaleString()}`;
            elements.historyList.appendChild(item);
        });
    }

    function renderUpgrades() {
        if (!elements.upgradesContent) {
            return;
        }
        if (!state.upgradeDefinitions.length) {
            elements.upgradesContent.innerHTML = '<p>Улучшения появятся позже. Добавьте их в <code>game/config.py</code>.</p>';
            return;
        }

        const list = document.createElement('ul');
        list.className = 'upgrades__list';

        state.upgradeDefinitions.forEach((definition) => {
            const item = document.createElement('li');
            item.className = 'upgrades__item';

            const title = document.createElement('h4');
            title.textContent = definition.name;

            const description = document.createElement('p');
            description.textContent = definition.description;

            const footer = document.createElement('div');
            footer.className = 'upgrades__footer';
            const price = document.createElement('span');
            price.textContent = `Цена: ${definition.base_cost} монет`;

            const purchased = state.upgrades.includes(definition.key);
            const action = document.createElement('button');
            action.className = 'btn btn--ghost';
            action.type = 'button';
            action.textContent = purchased ? 'Уже куплено' : 'Скоро';
            action.disabled = true;

            footer.appendChild(price);
            footer.appendChild(action);

            item.appendChild(title);
            item.appendChild(description);
            item.appendChild(footer);
            list.appendChild(item);
        });

        elements.upgradesContent.innerHTML = '';
        elements.upgradesContent.appendChild(list);
    }

    async function loadTasks(city) {
        if (!city) {
            return;
        }
        try {
            const response = await apiRequest(`/api/tasks/?city=${encodeURIComponent(city)}`);
            elements.tasksSection.removeAttribute('data-hidden');
            renderTasks(response.data.tasks);
        } catch (error) {
            elements.tasksSection.setAttribute('data-hidden', 'true');
            console.error(error);
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
            console.error(error);
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
        try {
            const response = await apiRequest('/api/weather/lookup/', {
                method: 'POST',
                body: JSON.stringify({ city }),
            });
            state.coins = response.data.coins;
            state.currentCity = response.data.weather.city;
            elements.weatherCityInput.value = state.currentCity;
            updateHud();
            renderWeather(response.data.weather);
            elements.tasksSection.removeAttribute('data-hidden');
            elements.historySection.removeAttribute('data-hidden');
            await loadTasks(state.currentCity);
            await loadHistory();
        } catch (error) {
            elements.weatherMessage.textContent = error.message;
        } finally {
            elements.weatherForm.classList.remove('is-loading');
        }
    }

    async function handleTaskSubmit(event) {
        event.preventDefault();
        const city = state.currentCity;
        if (!city) {
            alert('Сначала получите погоду города.');
            return;
        }
        const title = elements.taskTitle.value.trim();
        const notes = elements.taskNotes.value.trim();
        if (!title) {
            alert('Введите название задачи.');
            return;
        }
        try {
            await apiRequest('/api/tasks/', {
                method: 'POST',
                body: JSON.stringify({ city, title, notes }),
            });
            elements.taskTitle.value = '';
            elements.taskNotes.value = '';
            elements.taskForm.setAttribute('data-hidden', 'true');
            await loadTasks(city);
        } catch (error) {
            alert(error.message);
        }
    }

    function setupTaskForm() {
        elements.taskForm?.addEventListener('submit', handleTaskSubmit);
        elements.taskCancel?.addEventListener('click', () => {
            elements.taskForm.setAttribute('data-hidden', 'true');
        });
        elements.taskToggle?.addEventListener('click', () => {
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
            if (state.upgrades && state.upgrades.length) {
                renderUpgrades();
            }
            openModal(elements.upgradesModal);
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

    function setupWeatherForm() {
        elements.weatherForm?.addEventListener('submit', handleWeatherSubmit);
        elements.weatherPrice.textContent = state.weatherPrice;
    }

    function setupFloors() {
        recenterFloors(state.currentFloor);
        elements.floorContainer.addEventListener('scroll', handleScroll);
        window.addEventListener('resize', () => recenterFloors(state.currentFloor));
    }

    function init() {
        setupFloors();
        setupModals();
        setupWeatherForm();
        setupTaskForm();
        loadGameState();
        loadHistory();
    }

    document.addEventListener('DOMContentLoaded', init);
})();
