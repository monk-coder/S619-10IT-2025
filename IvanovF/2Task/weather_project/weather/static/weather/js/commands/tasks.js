// Fetches and prints the authenticated user's reminders.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('tasks', {
    helpEntry: 'tasks — показать сохранённые напоминания',
    execute: async () => {
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
    },
  });
})();
