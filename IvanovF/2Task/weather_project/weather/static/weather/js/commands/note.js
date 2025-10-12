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
      TerminalApp.addNote(args);
      const count = TerminalApp.getNotes().length;
      TerminalApp.print(`Note saved (#${count})`);
    },
  });
})();
