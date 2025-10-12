// Performs server-side logout and clears local state.
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
    },
  });
})();
