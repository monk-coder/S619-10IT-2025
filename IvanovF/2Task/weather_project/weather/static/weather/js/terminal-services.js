(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.getCurrentUtcMillis = () => {
    const { serverUtcMillis, syncPerfNow } = TerminalApp.getServerTimeRef();
    if (serverUtcMillis === null || syncPerfNow === null) {
      return Date.now() + new Date().getTimezoneOffset() * 60000;
    }
    return serverUtcMillis + (performance.now() - syncPerfNow);
  };

  TerminalApp.syncTime = async () => {
    try {
      const res = await fetch('/api/time/');
      const data = await res.json();
      let serverUtcMillis;
      if (typeof data.unixtime === 'number') {
        serverUtcMillis = data.unixtime * 1000;
      } else if (data.utc_datetime) {
        serverUtcMillis = Date.parse(data.utc_datetime);
      } else {
        serverUtcMillis = Date.now() + new Date().getTimezoneOffset() * 60000;
      }
      TerminalApp.setServerTimeRef(serverUtcMillis, performance.now());
      TerminalApp.updateClockDisplay();
    } catch (err) {
      const fallback = Date.now() + new Date().getTimezoneOffset() * 60000;
      TerminalApp.setServerTimeRef(fallback, performance.now());
      TerminalApp.updateClockDisplay();
    }
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
  };
})();
