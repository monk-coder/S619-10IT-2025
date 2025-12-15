// Команда clear полностью очищает вывод терминала.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('clear', {
    helpEntry: 'clear — очистить экран',
    execute: () => {
      // Сбрасываем DOM-историю и выводим подсказку пользователю.
      if (TerminalApp.elements.output) TerminalApp.elements.output.innerHTML = '';
      TerminalApp.print('Подсказка: введите "help" для списка команд.');
    },
  });
})();
