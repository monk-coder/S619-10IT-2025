// Точка входа фронтенд-терминала: инициализация UI и обработка ввода.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  // Навешиваем обработчики на поле ввода терминала.
  const attachInputListeners = () => {
    const { input } = TerminalApp.elements;
    if (!input) return;

    // Синхронизация курсора и подсказки выполняется в кадре анимации.
    const scheduleInputStateUpdate = () => requestAnimationFrame(() => {
      TerminalApp.updateCursorPosition();
      TerminalApp.refreshAutocompleteHint();
    });

    // Каждое изменение текста/фокуса приводит к пересчёту позиции курсора.
    ['input', 'keyup', 'click', 'focus', 'mouseup'].forEach((evt) => {
      input.addEventListener(evt, scheduleInputStateUpdate);
    });

    // При изменении размеров окна подсказка тоже перестраивается.
    window.addEventListener('resize', scheduleInputStateUpdate);

    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        // Tab не должен печатать символ, вместо этого вызываем автодополнение.
        TerminalApp.autocompleteCommand();
        scheduleInputStateUpdate();
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        // Считываем введённую команду, очищаем поле и запоминаем запрос в ленте.
        const raw = input.value.trim();
        input.value = '';
        scheduleInputStateUpdate();
        if (!raw) return;
        const user = TerminalApp.getCurrentUser() || 'guest';
        TerminalApp.print(`${user}@dash:~$ ${raw}`);
        try {
          // Отдаём строку в обработчик команд и ловим ошибки.
          await TerminalApp.executeCommand(raw);
        } catch (err) {
          TerminalApp.print(`Command error: ${err.message || err}`, 'error');
        }
        return;
      }

      // Для всех остальных клавиш просто пересчитываем курсор.
      scheduleInputStateUpdate();
    });
  };

  // Общая инициализация терминала: восстанавливаем состояние и запускаем таймеры.
  TerminalApp.init = () => {
    // Загружаем сохранённые данные и обновляем приглашение пользователя.
    TerminalApp.restoreState();
    TerminalApp.updatePrompt();
    TerminalApp.refreshAutocompleteHint();
    TerminalApp.renderHistory([]);
    // Первый приветственный вывод подсказывает пользователю начать с help.
    TerminalApp.print("Введите 'help' для списка команд.");
    requestAnimationFrame(() => {
      // После первого кадра положение курсора и подсказка совпадут с пустой строкой.
      TerminalApp.updateCursorPosition();
      TerminalApp.refreshAutocompleteHint();
    });
    // Проверяем авторизацию и подтягиваем историю/задачи.
    TerminalApp.syncAuthStatus();
    // Поддерживаем синхронизированные часы (UTC + оффсет).
    TerminalApp.syncTime();
    TerminalApp.updateClockDisplay();

    // Вешаем слушатели и периодически обновляем часы и серверное время.
    attachInputListeners();

    // Каждую секунду обновляем визуальные часы в заголовке.
    setInterval(() => {
      TerminalApp.updateClockDisplay();
    }, 1000);

    // Каждые 5 минут перепрашиваем серверное время, чтобы часы не уплывали.
    setInterval(() => {
      TerminalApp.syncTime();
    }, 5 * 60 * 1000);
  };

  // Инициализируем терминал сразу или ждём готовности DOM.
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', TerminalApp.init);
  } else {
    TerminalApp.init();
  }
})();
