// Команда help открывает общий список доступных команд.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('help', {
    helpEntry: 'help — показать список команд',
    execute: () => {
      // Просто делегируем вывод штатной функции справки.
      TerminalApp.showHelp();
    },
  });
})();
