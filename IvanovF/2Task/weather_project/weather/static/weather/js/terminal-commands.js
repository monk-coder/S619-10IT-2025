(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const helpItems = [
    'help',
    'login <логин> <пароль>',
    'signup <логин> <пароль>',
    'weather <city>',
    'flight <IATA>',
    'taskadd <город>|<текст>',
    'tasks',
    'taskupdate <id>|[город]|[текст]',
    'taskdelete <id>',
    'note <text>',
    'notes',
    'timer <seconds>',
    'timezone <offset>',
    'logout',
    'clear',
  ];

  const commandsList = Array.from(new Set(helpItems.map((item) => item.split(' ')[0])));
  const commandsWithArgs = new Set(['login', 'signup', 'weather', 'flight', 'note', 'taskadd', 'taskupdate', 'taskdelete', 'timer', 'timezone']);

  const asciiIcons = {
    sun: '  \\   /  \n   .-.   \n- (   ) -\n   `-’   \n  /   \\  ',
    cloud: '    .--.   \n .-(    ). \n(___.__)__)',
    rain: "    .--.   \n .-(    ). \n(___.__)__)\n ' ' ' ' ' ",
    snow: '    .--.   \n .-(    ). \n(___.__)__)\n  *  *  *  ',
    plane: '     __|__\n--@--@--(_)--@--@--',
  };

  TerminalApp.helpItems = helpItems;
  TerminalApp.asciiIcons = asciiIcons;

  TerminalApp.showHelp = () => {
    TerminalApp.print('Welcome to Terminal Dashboard');
    TerminalApp.printHtml('<span class="big">Terminal Dashboard</span>');
    TerminalApp.print('Available commands:');
    helpItems.forEach((entry) => TerminalApp.print(`- ${entry}`));
    TerminalApp.print('(Часы синхронизируются с реальным UTC временем через backend API.)');
  };

  TerminalApp.autocompleteCommand = () => {
    const input = TerminalApp.elements.input;
    if (!input) return;
    const value = input.value;
    const caretIndex = input.selectionStart ?? value.length;
    const beforeCaret = value.slice(0, caretIndex);
    if (beforeCaret.includes(' ')) return;
    const partial = beforeCaret.trim();
    if (!partial) return;
    const matches = commandsList.filter((cmd) => cmd.startsWith(partial));
    if (matches.length === 0) return;
    if (matches.length === 1) {
      const base = matches[0];
      const suffix = commandsWithArgs.has(base) ? ' ' : '';
      const completed = base + suffix;
      const rest = value.slice(caretIndex);
      input.value = completed + rest;
      const pos = completed.length;
      input.setSelectionRange(pos, pos);
      requestAnimationFrame(TerminalApp.updateCursorPosition);
    } else {
      TerminalApp.print(`Suggestions: ${matches.join('  ')}`);
    }
  };

  TerminalApp.executeCommand = async (raw) => {
    const parts = raw.split(/\s+/).filter(Boolean);
    if (parts.length === 0) return;
    const cmd = parts[0].toLowerCase();
    const arg = parts.slice(1).join(' ');

    if (cmd === 'help') {
      TerminalApp.showHelp();
      return;
    }

    if (cmd === 'clear') {
      if (TerminalApp.elements.output) TerminalApp.elements.output.innerHTML = '';
      return;
    }

    if (cmd === 'signup') {
      const [username, password] = (arg || '').split(/\s+/);
      if (!username || !password) {
        TerminalApp.print('Error: используйте signup <логин> <пароль>', 'error');
        return;
      }
      TerminalApp.print(`Создание аккаунта ${username}...`);
      try {
        const resp = await fetch('/api/auth/register/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ username, password }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser(data.username || username);
        TerminalApp.updatePrompt();
        TerminalApp.print(data.message || 'Регистрация завершена');
        await TerminalApp.fetchHistory();
        try {
          await TerminalApp.fetchTasks();
        } catch (err) {
          // ignore fetch errors here
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'login') {
      const [username, password] = (arg || '').split(/\s+/);
      if (!username || !password) {
        TerminalApp.print('Error: используйте login <логин> <пароль>', 'error');
        return;
      }
      TerminalApp.print(`Авторизация ${username}...`);
      try {
        const resp = await fetch('/api/auth/login/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ username, password }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser(data.username || username);
        TerminalApp.updatePrompt();
        TerminalApp.print(data.message || 'Авторизация успешна');
        await TerminalApp.fetchHistory();
        try {
          await TerminalApp.fetchTasks();
        } catch (err) {
          // ignore fetch errors here
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'timezone') {
      if (!arg) {
        TerminalApp.print('Error: provide offset, e.g. timezone +3 or timezone -5.5', 'error');
        return;
      }
      const val = parseFloat(arg);
      if (!Number.isFinite(val)) {
        TerminalApp.print('Error: invalid offset', 'error');
        return;
      }
      TerminalApp.setTimezoneOffset(val);
      TerminalApp.updateClockDisplay();
      const sign = val >= 0 ? '+' : '';
      TerminalApp.print(`Timezone set to UTC${sign}${val}`);
      return;
    }

    if (cmd === 'note') {
      if (!arg) {
        TerminalApp.print('Error: note text required', 'error');
        return;
      }
      TerminalApp.addNote(arg);
      const count = TerminalApp.getNotes().length;
      TerminalApp.print(`Note saved (#${count})`);
      return;
    }

    if (cmd === 'notes') {
      const notes = TerminalApp.getNotes();
      if (notes.length === 0) {
        TerminalApp.print('No notes yet.');
        return;
      }
      TerminalApp.print('Notes:');
      notes.forEach((n, i) => TerminalApp.print(`${i + 1}. ${n}`));
      return;
    }

    if (cmd === 'tasks') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      try {
        const tasks = await TerminalApp.fetchTasks();
        if (!tasks.length) {
          TerminalApp.print('Пока задач нет.');
          return;
        }
        TerminalApp.print('Ваши напоминания:');
        tasks.forEach((task) => {
          TerminalApp.print(TerminalApp.describeTask(task));
        });
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskadd') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = arg || '';
      const separatorIndex = rawArg.indexOf('|');
      if (separatorIndex === -1) {
        TerminalApp.print('Error: используйте taskadd <город>|<текст>', 'error');
        return;
      }
      const city = rawArg.slice(0, separatorIndex).trim();
      const text = rawArg.slice(separatorIndex + 1).trim();
      if (!city || !text) {
        TerminalApp.print('Error: укажите город и текст напоминания', 'error');
        return;
      }
      TerminalApp.print(`Сохранение задачи для ${city}...`);
      try {
        const resp = await fetch('/api/tasks/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ city, text }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        if (data.task) {
          TerminalApp.upsertTask(data.task);
          TerminalApp.print(`Задача #${data.task.id} сохранена.`);
          TerminalApp.print(TerminalApp.describeTask(data.task));
        } else {
          TerminalApp.print('Задача сохранена.');
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskupdate') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = arg || '';
      const firstSep = rawArg.indexOf('|');
      if (firstSep === -1) {
        TerminalApp.print('Error: используйте taskupdate <id>|<город>|<текст>', 'error');
        return;
      }
      const secondPart = rawArg.slice(firstSep + 1);
      const secondSep = secondPart.indexOf('|');
      if (secondSep === -1) {
        TerminalApp.print('Error: используйте taskupdate <id>|<город>|<текст>', 'error');
        return;
      }
      const idPart = rawArg.slice(0, firstSep).trim();
      const city = secondPart.slice(0, secondSep).trim();
      const text = secondPart.slice(secondSep + 1).trim();
      const id = Number(idPart);
      if (!Number.isInteger(id) || id <= 0) {
        TerminalApp.print('Error: некорректный идентификатор задачи', 'error');
        return;
      }
      if (!city || !text) {
        TerminalApp.print('Error: укажите город и текст для обновления', 'error');
        return;
      }
      TerminalApp.print(`Обновление задачи #${id}...`);
      try {
        const resp = await fetch(`/api/tasks/${id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ city, text }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        if (data.task) {
          TerminalApp.upsertTask(data.task);
          TerminalApp.print(`Задача #${data.task.id} обновлена.`);
          TerminalApp.print(TerminalApp.describeTask(data.task));
        } else {
          TerminalApp.print('Задача обновлена.');
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskdelete') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const id = Number((arg || '').trim());
      if (!Number.isInteger(id) || id <= 0) {
        TerminalApp.print('Error: используйте taskdelete <id>', 'error');
        return;
      }
      TerminalApp.print(`Удаление задачи #${id}...`);
      try {
        const resp = await fetch(`/api/tasks/${id}/`, {
          method: 'DELETE',
          credentials: 'same-origin',
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          TerminalApp.print(`Error: ${(data && data.error) || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.removeTask(id);
        TerminalApp.print('Задача удалена.');
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'timer') {
      if (!arg || Number.isNaN(Number(arg))) {
        TerminalApp.print('Error: seconds required', 'error');
        return;
      }
      let sec = Math.max(0, Math.floor(Number(arg)));
      TerminalApp.clearTimerInterval();
      TerminalApp.print(`Timer started: ${sec} seconds`);
      const interval = setInterval(() => {
        if (sec <= 0) {
          clearInterval(interval);
          TerminalApp.clearTimerInterval();
          TerminalApp.print('⏰ Timer finished!', 'big');
        } else {
          TerminalApp.print(`... ${sec} sec left`);
          sec -= 1;
        }
      }, 1000);
      TerminalApp.setTimerInterval(interval);
      return;
    }

    if (cmd === 'logout') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Вы не вошли в систему.');
        return;
      }
      const username = TerminalApp.getCurrentUser();
      TerminalApp.print(`Выход из аккаунта ${username}...`);
      try {
        const resp = await fetch('/api/auth/logout/', {
          method: 'POST',
          credentials: 'same-origin',
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser('guest');
        TerminalApp.updatePrompt();
        TerminalApp.setTasks([]);
        TerminalApp.print(data.message || 'Вы вышли из системы.');
        await TerminalApp.fetchHistory();
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'weather') {
      if (!arg) {
        TerminalApp.print('Error: city required', 'error');
        return;
      }
      TerminalApp.print(`Fetching weather for ${arg}...`);
      try {
        const resp = await fetch(`/api/weather/?city=${encodeURIComponent(arg)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        const description = (data.description || '').toLowerCase();
        let icon = asciiIcons.sun;
        if (description.includes('дожд')) icon = asciiIcons.rain;
        else if (description.includes('снег')) icon = asciiIcons.snow;
        else if (description.includes('облач')) icon = asciiIcons.cloud;
        TerminalApp.printHtml(`<pre style="margin:0;color:#0f0;">${icon}</pre>`);
        TerminalApp.print(`${(data.city || '').toUpperCase()}`, 'big');
        TerminalApp.print(`Температура: ${data.temperature}°C`);
        TerminalApp.print(`Влажность: ${data.humidity}%`);
        TerminalApp.print(`Описание: ${data.description}`);
        if (TerminalApp.getCurrentUser() !== 'guest') {
          TerminalApp.fetchHistory();
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'flight') {
      if (!arg) {
        TerminalApp.print('Error: airport IATA required', 'error');
        return;
      }
      TerminalApp.print(`Fetching flight for ${arg.toUpperCase()}...`);
      try {
        const resp = await fetch(`/api/flight/?airport=${encodeURIComponent(arg)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.printHtml(`<pre style="margin:0;color:#0f0;">${asciiIcons.plane}</pre>`);
        TerminalApp.print(`Рейс: ${data.flight_number}`, 'big');
        TerminalApp.print(`Авиакомпания: ${data.airline}`);
        TerminalApp.print(`Статус: ${data.status}`);
        TerminalApp.print(`Вылет: ${data.departure_airport} @ ${data.departure_time || 'N/A'}`);
        TerminalApp.print(`Прилет: ${data.arrival_airport} @ ${data.arrival_time || 'N/A'}`);
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    TerminalApp.print(`Unknown command: ${cmd}`, 'error');
  };
})();
