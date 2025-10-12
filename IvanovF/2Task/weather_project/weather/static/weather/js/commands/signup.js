(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('signup', {
    helpEntry: 'signup <логин> <пароль> — зарегистрироваться',
    requiresArgs: true,
    execute: async ({ args }) => {
      const [username, password] = (args || '').split(/\s+/);
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
    },
  });
})();
