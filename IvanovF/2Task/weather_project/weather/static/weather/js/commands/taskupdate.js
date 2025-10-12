(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('taskupdate', {
    helpEntry: 'taskupdate <id>|[город]|[текст] — изменить напоминание',
    requiresArgs: true,
    execute: async ({ args }) => {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = args || '';
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
    },
  });
})();
