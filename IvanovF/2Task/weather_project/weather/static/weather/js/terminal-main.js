(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const attachInputListeners = () => {
    const { input } = TerminalApp.elements;
    if (!input) return;

    const scheduleInputStateUpdate = () => requestAnimationFrame(() => {
      TerminalApp.updateCursorPosition();
      TerminalApp.refreshAutocompleteHint();
    });

    ['input', 'keyup', 'click', 'focus', 'mouseup'].forEach((evt) => {
      input.addEventListener(evt, scheduleInputStateUpdate);
    });

    window.addEventListener('resize', scheduleInputStateUpdate);

    input.addEventListener('keydown', async (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        TerminalApp.autocompleteCommand();
        scheduleInputStateUpdate();
        return;
      }

      if (e.key === 'Enter') {
        e.preventDefault();
        const raw = input.value.trim();
        input.value = '';
        scheduleInputStateUpdate();
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

      scheduleInputStateUpdate();
    });
  };

  TerminalApp.init = () => {
    TerminalApp.restoreState();
    TerminalApp.updatePrompt();
    TerminalApp.refreshAutocompleteHint();
    TerminalApp.renderHistory([]);
    TerminalApp.print("Введите 'help' для списка команд.");
    requestAnimationFrame(() => {
      TerminalApp.updateCursorPosition();
      TerminalApp.refreshAutocompleteHint();
    });
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
