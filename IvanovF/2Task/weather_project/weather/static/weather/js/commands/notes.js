(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('notes', {
    helpEntry: 'notes — показать локальные заметки',
    execute: () => {
      const notes = TerminalApp.getNotes();
      if (notes.length === 0) {
        TerminalApp.print('No notes yet.');
        return;
      }
      TerminalApp.print('Notes:');
      notes.forEach((n, i) => TerminalApp.print(`${i + 1}. ${n}`));
    },
  });
})();
