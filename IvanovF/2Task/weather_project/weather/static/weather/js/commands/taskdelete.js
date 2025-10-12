(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('taskdelete', {
    helpEntry: 'taskdelete <id> — удалить напоминание',
    requiresArgs: true,
    execute: async ({ args }) => {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const id = Number((args || '').trim());
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
    },
  });
})();
