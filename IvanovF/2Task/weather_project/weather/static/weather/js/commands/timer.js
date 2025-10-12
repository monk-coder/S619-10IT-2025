(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('timer', {
    helpEntry: 'timer <секунды> — запустить таймер',
    requiresArgs: true,
    execute: ({ args }) => {
      if (!args || Number.isNaN(Number(args))) {
        TerminalApp.print('Error: seconds required', 'error');
        return;
      }
      let sec = Math.max(0, Math.floor(Number(args)));
      TerminalApp.clearTimerInterval();
      const { output } = TerminalApp.elements;
      if (!output) {
        TerminalApp.print('Error: terminal unavailable', 'error');
        return;
      }

      let line = TerminalApp.__activeTimerLine;
      if (!line || !line.isConnected) {
        line = document.createElement('div');
        line.className = 'timer-line';
        output.appendChild(line);
        TerminalApp.__activeTimerLine = line;
      } else {
        output.appendChild(line);
      }

      const plural = (value) => (value === 1 ? '' : 's');
      const updateLine = (text) => {
        line.textContent = text;
        output.scrollTop = output.scrollHeight;
      };

      updateLine(`Timer started: ${sec} second${plural(sec)}`);

      if (sec === 0) {
        updateLine('⏰ Timer finished!');
        return;
      }

      const interval = setInterval(() => {
        sec -= 1;
        if (sec <= 0) {
          TerminalApp.clearTimerInterval();
          updateLine('⏰ Timer finished!');
          return;
        }
        updateLine(`Timer: ${sec} second${plural(sec)}`);
      }, 1000);
      TerminalApp.setTimerInterval(interval);
    },
  });
})();
