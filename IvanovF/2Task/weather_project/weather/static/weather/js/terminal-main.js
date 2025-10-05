(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const attachInputListeners = () => {
    const { input } = TerminalApp.elements;
    if (!input) return;

    ['input', 'keyup', 'click', 'focus', 'mouseup'].forEach((evt) => {
      input.addEventListener(evt, () => requestAnimationFrame(TerminalApp.updateCursorPosition));
    });

    window.addEventListener('resize', () => requestAnimationFrame(TerminalApp.updateCursorPosition));

    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        TerminalApp.autocompleteCommand();
        requestAnimationFrame(TerminalApp.updateCursorPosition);
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        const raw = input.value.trim();
        input.value = '';
        requestAnimationFrame(TerminalApp.updateCursorPosition);
        if (!raw) return;
        const user = TerminalApp.getCurrentUser() || 'guest';
        TerminalApp.print(`${user}@dash:~$ ${raw}`);
        try {
          await TerminalApp.executeCommand(raw);
        } catch (err) {
          TerminalApp.print(`Command error: ${err.message || err}`, 'error');
        }
        return;
      }

      requestAnimationFrame(TerminalApp.updateCursorPosition);
    });
  };

  TerminalApp.init = () => {
    TerminalApp.restoreState();
    TerminalApp.updatePrompt();
    TerminalApp.renderHistory([]);
    TerminalApp.print("Введите 'help' для списка команд.");
    requestAnimationFrame(TerminalApp.updateCursorPosition);
    TerminalApp.syncAuthStatus();
    TerminalApp.syncTime();
    TerminalApp.updateClockDisplay();

    attachInputListeners();

    setInterval(() => {
      TerminalApp.updateClockDisplay();
    }, 1000);

    setInterval(() => {
      TerminalApp.syncTime();
    }, 5 * 60 * 1000);
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', TerminalApp.init);
  } else {
    TerminalApp.init();
  }
})();
