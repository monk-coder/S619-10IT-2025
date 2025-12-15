// Этот модуль описывает простые сервисные функции: время, историю и задачи.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  // Возвращаем текущее время по UTC для расчётов часов.
  TerminalApp.getCurrentUtcMillis = () => {
    return Date.now();
  };

  // Обновляем ссылку на серверное время и сразу перерисовываем часы.
  TerminalApp.syncTime = async () => {
    const utcMillis = Date.now();
    TerminalApp.setServerTimeRef(utcMillis, performance.now());
    TerminalApp.updateClockDisplay();
    return utcMillis;
  };

  // Загружаем историю запросов для авторизованного пользователя.
  TerminalApp.fetchHistory = async () => {
    if (!TerminalApp.elements.historyList) return;
    if (TerminalApp.getCurrentUser() === 'guest') {
      // Для гостей сервер не хранит историю — показываем пустой список.
      TerminalApp.renderHistory([]);
      return;
    }

    try {
      const resp = await fetch('/api/history/', { credentials: 'same-origin' });
      // В случае любой сетевой ошибки просто падаем в catch.
      if (!resp.ok) throw new Error('history request failed');
      const data = await resp.json();
      const entries = Array.isArray(data.entries) ? data.entries : [];
      TerminalApp.renderHistory(entries);
    } catch (err) {
      // Ошибку проглатываем — пользователь просто увидит пустую историю.
      TerminalApp.renderHistory([]);
    }
  };

  // Запрашиваем активные задачи пользователя и сохраняем их в состоянии.
  TerminalApp.fetchTasks = async () => {
    if (TerminalApp.getCurrentUser() === 'guest') {
      TerminalApp.setTasks([]);
      return [];
    }

    try {
      const resp = await fetch('/api/tasks/', { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('tasks request failed');
      const data = await resp.json();
      const tasks = Array.isArray(data.tasks) ? data.tasks : [];
      TerminalApp.setTasks(tasks);
      return tasks;
    } catch (err) {
      // Если не удалось загрузить задачи, лучше очистить локальный список.
      TerminalApp.setTasks([]);
      throw err;
    }
  };

  // Узнаём статус авторизации и подтягиваем историю/задачи при успехе.
  TerminalApp.syncAuthStatus = async () => {
    try {
      const resp = await fetch('/api/auth/status/', { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('status request failed');
      const data = await resp.json();
      if (data.authenticated && data.username) {
        // Пользователь авторизован — фиксируем его имя.
        TerminalApp.setCurrentUser(data.username);
      } else {
        TerminalApp.setCurrentUser('guest');
      }
    } catch (err) {
      // При ошибке запроса возвращаемся в гостьевой режим.
      TerminalApp.setCurrentUser('guest');
    }
    // После обновления пользователя пересчитываем приглашение.
    TerminalApp.updatePrompt();
    // История нужна для сайдбара — подгружаем её всегда.
    // Ошибки fetchHistory нас не интересуют: функция сама покажет пустоту.
    await TerminalApp.fetchHistory();
    try {
      await TerminalApp.fetchTasks();
    } catch (err) {
      // ignore task fetch errors during auth sync
    }
  };
})();