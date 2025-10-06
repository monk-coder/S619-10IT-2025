(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const elements = {
    output: document.getElementById('output'),
    input: document.getElementById('cmdline'),
    clock: document.getElementById('clock'),
    cursor: document.querySelector('.cursor'),
    measure: document.getElementById('caret-measure'),
    promptLabel: document.getElementById('prompt-label'),
    historyList: document.getElementById('history-list'),
  };

  TerminalApp.elements = elements;

  const state = {
    notes: [],
    tasks: [],
    timezoneOffset: 0,
    timerInterval: null,
    currentUser: 'guest',
    serverUtcMillis: null,
    syncPerfNow: null,
  };

  TerminalApp.state = state;

  TerminalApp.restoreState = () => {
    try {
      state.notes = JSON.parse(localStorage.getItem('terminal_notes') || '[]');
      if (!Array.isArray(state.notes)) state.notes = [];
    } catch (err) {
      state.notes = [];
    }

    const storedTz = localStorage.getItem('terminal_tz');
    if (storedTz === null) {
      const deviceOffset = -new Date().getTimezoneOffset() / 60;
      state.timezoneOffset = deviceOffset;
      localStorage.setItem('terminal_tz', String(deviceOffset));
    } else {
      state.timezoneOffset = parseFloat(storedTz) || 0;
    }
  };

  TerminalApp.setTasks = (tasks) => {
    state.tasks = Array.isArray(tasks) ? tasks.slice() : [];
  };

  TerminalApp.getTasks = () => state.tasks.slice();

  TerminalApp.upsertTask = (task) => {
    if (!task || typeof task.id !== 'number') return;
    const index = state.tasks.findIndex((item) => item.id === task.id);
    if (index === -1) {
      state.tasks.unshift(task);
    } else {
      state.tasks[index] = task;
    }
  };

  TerminalApp.removeTask = (taskId) => {
    state.tasks = state.tasks.filter((item) => item.id !== taskId);
  };

  TerminalApp.describeTask = (task) => {
    if (!task) return '';
    const created = task.created_at ? ` @ ${TerminalApp.formatHistoryTime(task.created_at)}` : '';
    return `[${task.id}] ${task.city}: ${task.text}${created}`;
  };

  TerminalApp.saveNotes = () => {
    localStorage.setItem('terminal_notes', JSON.stringify(state.notes));
  };

  TerminalApp.addNote = (note) => {
    state.notes.push(note);
    TerminalApp.saveNotes();
  };

  TerminalApp.getNotes = () => state.notes.slice();

  TerminalApp.setTimezoneOffset = (value) => {
    state.timezoneOffset = value;
    localStorage.setItem('terminal_tz', String(value));
  };

  TerminalApp.getTimezoneOffset = () => state.timezoneOffset;

  TerminalApp.setTimerInterval = (interval) => {
    if (state.timerInterval) clearInterval(state.timerInterval);
    state.timerInterval = interval;
  };

  TerminalApp.clearTimerInterval = () => {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  };

  TerminalApp.getCurrentUser = () => state.currentUser;

  TerminalApp.setCurrentUser = (user) => {
    state.currentUser = user || 'guest';
  };

  TerminalApp.setServerTimeRef = (serverMillis, perfNow) => {
    state.serverUtcMillis = serverMillis;
    state.syncPerfNow = perfNow;
  };

  TerminalApp.getServerTimeRef = () => ({
    serverUtcMillis: state.serverUtcMillis,
    syncPerfNow: state.syncPerfNow,
  });

  TerminalApp.pad2 = (n) => String(n).padStart(2, '0');

  TerminalApp.updateCursorPosition = () => {
    const { input, cursor, measure } = elements;
    if (!input || !cursor || !measure) return;
    const value = input.value || '';
    const caretIndex = input.selectionStart ?? value.length;
    const beforeCaret = value.slice(0, caretIndex).replace(/ /g, '\u00a0') || '\u200b';
    measure.textContent = beforeCaret;
    const caretLeft = measure.offsetWidth - input.scrollLeft;
    cursor.style.left = `${Math.max(0, caretLeft)}px`;
  };

  TerminalApp.updatePrompt = () => {
    if (!elements.promptLabel) return;
    const userLabel = TerminalApp.getCurrentUser() || 'guest';
    elements.promptLabel.textContent = `${userLabel}@dash:~$`;
  };

  TerminalApp.print = (text, cls = '') => {
    if (!elements.output) return;
    const div = document.createElement('div');
    if (cls) div.className = cls;
    div.textContent = text;
    elements.output.appendChild(div);
    elements.output.scrollTop = elements.output.scrollHeight;
  };

  TerminalApp.printHtml = (html, cls = '') => {
    if (!elements.output) return;
    const div = document.createElement('div');
    if (cls) div.className = cls;
    div.innerHTML = html;
    elements.output.appendChild(div);
    elements.output.scrollTop = elements.output.scrollHeight;
  };

  TerminalApp.formatHistoryTime = (timestamp) => {
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return '';
    return date.toLocaleString(undefined, {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  TerminalApp.renderHistory = (entries) => {
    const list = elements.historyList;
    if (!list) return;
    list.innerHTML = '';

    if (TerminalApp.getCurrentUser() === 'guest') {
      const info = document.createElement('div');
      info.className = 'history-empty';
      info.textContent = 'Войдите, чтобы видеть историю запросов.';
      list.appendChild(info);
      return;
    }

    if (!entries || entries.length === 0) {
      const info = document.createElement('div');
      info.className = 'history-empty';
      info.textContent = 'История пока пуста.';
      list.appendChild(info);
      return;
    }

    entries.forEach((entry) => {
      const item = document.createElement('div');
      item.className = 'history-item';

      const city = document.createElement('div');
      city.className = 'history-item-city';
      city.textContent = entry.city;

      const time = document.createElement('div');
      time.className = 'history-item-time';
      time.textContent = TerminalApp.formatHistoryTime(entry.created_at);

      item.appendChild(city);
      if (time.textContent) item.appendChild(time);
      list.appendChild(item);
    });
  };

  TerminalApp.updateClockDisplay = () => {
    if (!elements.clock) return;
    const timezoneOffset = TerminalApp.getTimezoneOffset();
    const sign = timezoneOffset >= 0 ? '+' : '';
    const utcMillis = TerminalApp.getCurrentUtcMillis ? TerminalApp.getCurrentUtcMillis() : Date.now();
    const tzMillis = utcMillis + timezoneOffset * 3600000;
    const d = new Date(tzMillis);
    const Y = d.getUTCFullYear();
    const M = TerminalApp.pad2(d.getUTCMonth() + 1);
    const D = TerminalApp.pad2(d.getUTCDate());
    const h = TerminalApp.pad2(d.getUTCHours());
    const m = TerminalApp.pad2(d.getUTCMinutes());
    const s = TerminalApp.pad2(d.getUTCSeconds());
    elements.clock.textContent = `UTC${sign}${timezoneOffset} ${Y}-${M}-${D} ${h}:${m}:${s}`;
  };
})();
