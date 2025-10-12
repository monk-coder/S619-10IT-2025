// Clears terminal history for a fresh screen.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('clear', {
    helpEntry: 'clear — очистить экран',
    execute: () => {
      if (TerminalApp.elements.output) TerminalApp.elements.output.innerHTML = '';
      TerminalApp.print('Подсказка: введите "help" для списка команд.');
    },
  });
})();
