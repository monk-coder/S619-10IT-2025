// Команда tasks загружает и показывает задачи текущего пользователя.
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
        // Берём актуальный список с сервера и выводим его.
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
