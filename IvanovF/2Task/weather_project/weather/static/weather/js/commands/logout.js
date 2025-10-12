// Команда logout разлогинивает пользователя и очищает локальные данные.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('logout', {
    helpEntry: 'logout — выйти из аккаунта',
    execute: async () => {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Вы не вошли в систему.');
        return;
      }
      const username = TerminalApp.getCurrentUser();
      TerminalApp.print(`Выход из аккаунта ${username}...`);
      try {
        // Вызываем серверный logout и проверяем ответ.
        const resp = await fetch('/api/auth/logout/', {
          method: 'POST',
          credentials: 'same-origin',
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        // Возвращаем терминал в гостьевой режим.
        TerminalApp.setCurrentUser('guest');
        TerminalApp.updatePrompt();
        TerminalApp.setTasks([]);
        TerminalApp.print(data.message || 'Вы вышли из системы.');
        await TerminalApp.fetchHistory();
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
    },
  });
})();
