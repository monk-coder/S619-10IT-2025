(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('taskadd', {
    helpEntry: 'taskadd <город>|<текст> — сохранить напоминание по погоде',
    requiresArgs: true,
    execute: async ({ args }) => {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = args || '';
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
    },
  });
})();
