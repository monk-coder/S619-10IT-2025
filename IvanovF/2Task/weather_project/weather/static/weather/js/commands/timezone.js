(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('timezone', {
    helpEntry: 'timezone <смещение> — сменить пояс, например timezone +3',
    requiresArgs: true,
    execute: ({ args }) => {
      if (!args) {
        TerminalApp.print('Error: provide offset, e.g. timezone +3 or timezone -5.5', 'error');
        return;
      }
      const val = parseFloat(args);
      if (!Number.isFinite(val)) {
        TerminalApp.print('Error: invalid offset', 'error');
        return;
      }
      TerminalApp.setTimezoneOffset(val);
      TerminalApp.updateClockDisplay();
      const sign = val >= 0 ? '+' : '';
      TerminalApp.print(`Timezone set to UTC${sign}${val}`);
    },
  });
})();
