// Команда note добавляет локальную заметку в браузерное хранилище.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('note', {
    helpEntry: 'note <текст> — добавить локальную заметку',
    requiresArgs: true,
    execute: ({ args }) => {
      if (!args) {
        TerminalApp.print('Error: note text required', 'error');
        return;
      }
      // Сохраняем запись и сообщаем её порядковый номер.
      TerminalApp.addNote(args);
      const count = TerminalApp.getNotes().length;
      TerminalApp.print(`Note saved (#${count})`);
    },
  });
})();
