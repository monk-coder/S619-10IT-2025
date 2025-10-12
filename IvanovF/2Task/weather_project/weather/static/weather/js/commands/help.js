(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('help', {
    helpEntry: 'help — показать список команд',
    execute: () => {
      TerminalApp.showHelp();
    },
  });
})();
