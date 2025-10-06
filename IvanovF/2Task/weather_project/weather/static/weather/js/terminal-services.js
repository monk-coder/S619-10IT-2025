(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.getCurrentUtcMillis = () => {
    return Date.now();
  };

  TerminalApp.syncTime = async () => {
    const utcMillis = Date.now();
    TerminalApp.setServerTimeRef(utcMillis, performance.now());
    TerminalApp.updateClockDisplay();
    return utcMillis;
  };

  TerminalApp.fetchHistory = async () => {
    if (!TerminalApp.elements.historyList) return;
    if (TerminalApp.getCurrentUser() === 'guest') {
      TerminalApp.renderHistory([]);
      return;
    }

    try {
      const resp = await fetch('/api/history/', { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('history request failed');
      const data = await resp.json();
      const entries = Array.isArray(data.entries) ? data.entries : [];
      TerminalApp.renderHistory(entries);
    } catch (err) {
      TerminalApp.renderHistory([]);
    }
  };

  TerminalApp.fetchTasks = async () => {
    if (TerminalApp.getCurrentUser() === 'guest') {
      TerminalApp.setTasks([]);
      return [];
    }

    try {
      const resp = await fetch('/api/tasks/', { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('tasks request failed');
      const data = await resp.json();
      const tasks = Array.isArray(data.tasks) ? data.tasks : [];
      TerminalApp.setTasks(tasks);
      return tasks;
    } catch (err) {
      TerminalApp.setTasks([]);
      throw err;
    }
  };

  TerminalApp.syncAuthStatus = async () => {
    try {
      const resp = await fetch('/api/auth/status/', { credentials: 'same-origin' });
      if (!resp.ok) throw new Error('status request failed');
      const data = await resp.json();
      if (data.authenticated && data.username) {
        TerminalApp.setCurrentUser(data.username);
      } else {
        TerminalApp.setCurrentUser('guest');
      }
    } catch (err) {
      TerminalApp.setCurrentUser('guest');
    }
    TerminalApp.updatePrompt();
    await TerminalApp.fetchHistory();
    try {
      await TerminalApp.fetchTasks();
    } catch (err) {
      // ignore task fetch errors during auth sync
    }
  };
})();
