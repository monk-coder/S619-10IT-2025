(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('login', {
    helpEntry: 'login <логин> <пароль> — войти в аккаунт',
    requiresArgs: true,
    execute: async ({ args }) => {
      const [username, password] = (args || '').split(/\s+/);
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
    },
  });
})();
