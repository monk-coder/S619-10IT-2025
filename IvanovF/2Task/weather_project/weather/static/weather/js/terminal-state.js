(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const elements = {
    output: document.getElementById('output'),
    input: document.getElementById('cmdline'),
    hint: document.getElementById('cmdline-hint'),
    clock: document.getElementById('clock'),
    cursor: document.querySelector('.cursor'),
    measure: document.getElementById('caret-measure'),
    promptLabel: document.getElementById('prompt-label'),
    historyList: document.getElementById('history-list'),
  };

  TerminalApp.elements = elements;

  const CASINO_STORAGE_KEY = 'terminal_casino_state';
  const CASINO_DEFAULT_BALANCE = 100;
  const CASINO_DEFAULT_STAKE = 10;

  const state = {
    notes: [],
    tasks: [],
    currencySession: null,
    timezoneOffset: 0,
    timerInterval: null,
    currentUser: 'guest',
    serverUtcMillis: null,
    syncPerfNow: null,
    casino: {
      balance: CASINO_DEFAULT_BALANCE,
      initialBalance: CASINO_DEFAULT_BALANCE,
      ageConfirmed: false,
      ageValue: null,
      awaitingAge: false,
      awaitingReplay: false,
      awaitingSpin: false,
      awaitingMode: false,
      pendingMode: null,
      lastMode: 'roulette',
      stake: CASINO_DEFAULT_STAKE,
      bet: { type: null, value: null, stake: CASINO_DEFAULT_STAKE },
    },
  };

  TerminalApp.state = state;

  TerminalApp.restoreState = () => {
    try {
      state.notes = JSON.parse(localStorage.getItem('terminal_notes') || '[]');
      if (!Array.isArray(state.notes)) state.notes = [];
    } catch (err) {
      state.notes = [];
    }

    try {
      const storedCasino = JSON.parse(localStorage.getItem(CASINO_STORAGE_KEY) || '{}');
      if (storedCasino && typeof storedCasino === 'object') {
        const initial = Number(storedCasino.initialBalance);
        const balance = Number(storedCasino.balance);
        const stake = Number(storedCasino.stake);
        state.casino.initialBalance = Number.isFinite(initial) && initial > 0 ? Math.floor(initial) : CASINO_DEFAULT_BALANCE;
        state.casino.balance = Number.isFinite(balance) && balance >= 0 ? Math.floor(balance) : state.casino.initialBalance;
        state.casino.ageConfirmed = Boolean(storedCasino.ageConfirmed);
        const storedAgeValue = Number(storedCasino.ageValue);
        state.casino.ageValue = Number.isFinite(storedAgeValue) && storedAgeValue > 0 ? Math.floor(storedAgeValue) : null;
        state.casino.awaitingAge = Boolean(storedCasino.awaitingAge);
        state.casino.awaitingReplay = Boolean(storedCasino.awaitingReplay);
        state.casino.awaitingSpin = Boolean(storedCasino.awaitingSpin);
        state.casino.awaitingMode = Boolean(storedCasino.awaitingMode);
        state.casino.pendingMode = storedCasino.pendingMode || null;
        state.casino.lastMode = storedCasino.lastMode || 'roulette';
        state.casino.stake = Number.isFinite(stake) && stake > 0 ? Math.floor(stake) : CASINO_DEFAULT_STAKE;
        if (storedCasino.bet && typeof storedCasino.bet === 'object') {
          const betStake = Number(storedCasino.bet.stake);
          state.casino.bet = {
            type: storedCasino.bet.type || null,
            value: storedCasino.bet.value ?? null,
            stake: Number.isFinite(betStake) && betStake > 0 ? Math.floor(betStake) : state.casino.stake,
          };
        }
      }
    } catch (err) {
      state.casino.initialBalance = CASINO_DEFAULT_BALANCE;
      state.casino.balance = CASINO_DEFAULT_BALANCE;
      state.casino.ageConfirmed = false;
      state.casino.ageValue = null;
      state.casino.awaitingAge = false;
      state.casino.awaitingReplay = false;
      state.casino.awaitingSpin = false;
      state.casino.awaitingMode = false;
      state.casino.pendingMode = null;
      state.casino.lastMode = 'roulette';
      state.casino.stake = CASINO_DEFAULT_STAKE;
      state.casino.bet = { type: null, value: null, stake: CASINO_DEFAULT_STAKE };
    }

    if (!Number.isFinite(state.casino.initialBalance) || state.casino.initialBalance <= 0) {
      state.casino.initialBalance = CASINO_DEFAULT_BALANCE;
    }
    if (!Number.isFinite(state.casino.balance) || state.casino.balance < 0) {
      state.casino.balance = state.casino.initialBalance;
    }
    if (typeof state.casino.ageConfirmed !== 'boolean') {
      state.casino.ageConfirmed = false;
    }
    if (!Number.isFinite(state.casino.ageValue) || state.casino.ageValue <= 0) {
      state.casino.ageValue = null;
    }
    if (typeof state.casino.awaitingAge !== 'boolean') {
      state.casino.awaitingAge = false;
    }
    if (typeof state.casino.awaitingReplay !== 'boolean') {
      state.casino.awaitingReplay = false;
    }
    if (typeof state.casino.awaitingSpin !== 'boolean') {
      state.casino.awaitingSpin = false;
    }
    if (typeof state.casino.awaitingMode !== 'boolean') {
      state.casino.awaitingMode = false;
    }
    if (typeof state.casino.pendingMode !== 'string') {
      state.casino.pendingMode = null;
    }
    if (typeof state.casino.lastMode !== 'string' || !state.casino.lastMode) {
      state.casino.lastMode = 'roulette';
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

  TerminalApp.setCurrencySession = (session) => {
    state.currencySession = session;
  };

  TerminalApp.getCurrencySession = () => state.currencySession;

  TerminalApp.clearCurrencySession = () => {
    state.currencySession = null;
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

  const saveCasinoState = () => {
    try {
      localStorage.setItem(CASINO_STORAGE_KEY, JSON.stringify(state.casino));
    } catch (err) {
      // ignore storage errors
    }
  };

  TerminalApp.getCasinoState = () => ({ ...state.casino });

  TerminalApp.adjustCasinoBalance = (delta) => {
    const next = Math.max(0, Math.floor(state.casino.balance + delta));
    state.casino.balance = next;
    saveCasinoState();
    return next;
  };

  TerminalApp.resetCasinoBalance = () => {
    state.casino.balance = state.casino.initialBalance;
    saveCasinoState();
    return state.casino.balance;
  };

  TerminalApp.setCasinoInitialBalance = (value) => {
    if (Number.isFinite(value) && value > 0) {
      state.casino.initialBalance = Math.floor(value);
      if (state.casino.balance > state.casino.initialBalance) {
        state.casino.balance = state.casino.initialBalance;
      }
      saveCasinoState();
    }
  };

  TerminalApp.getCasinoStake = () => state.casino.stake;

  TerminalApp.setCasinoStake = (value) => {
    if (Number.isFinite(value) && value > 0) {
      state.casino.stake = Math.floor(value);
      if (!state.casino.bet) {
        state.casino.bet = { type: null, value: null, stake: state.casino.stake };
      } else {
        state.casino.bet.stake = state.casino.stake;
      }
      saveCasinoState();
    }
  };

  const clampCasinoAge = (value) => {
    if (!Number.isFinite(value)) return null;
    const normalized = Math.floor(value);
    if (normalized <= 0) return null;
    return Math.min(normalized, 120);
  };

  TerminalApp.confirmCasinoAge = (ageValue = null) => {
    const normalizedAge = clampCasinoAge(ageValue);
    state.casino.ageConfirmed = true;
    state.casino.ageValue = normalizedAge;
    saveCasinoState();
  };

  TerminalApp.revokeCasinoAge = () => {
    state.casino.ageConfirmed = false;
    state.casino.ageValue = null;
    saveCasinoState();
  };

  TerminalApp.getCasinoAgeValue = () => (Number.isFinite(state.casino.ageValue) ? state.casino.ageValue : null);

  TerminalApp.isCasinoAgeConfirmed = () => state.casino.ageConfirmed;

  TerminalApp.setCasinoPendingMode = (mode) => {
    state.casino.pendingMode = mode || null;
    saveCasinoState();
  };

  TerminalApp.getCasinoPendingMode = () => state.casino.pendingMode;

  TerminalApp.setCasinoLastMode = (mode) => {
    if (mode) {
      state.casino.lastMode = mode;
    }
  };

  TerminalApp.getCasinoLastMode = () => state.casino.lastMode || 'roulette';

  TerminalApp.setCasinoBet = (bet) => {
    if (!bet || typeof bet !== 'object') {
      state.casino.bet = { type: null, value: null, stake: state.casino.stake };
    } else {
      const stake = Number.isFinite(bet.stake) && bet.stake > 0 ? Math.floor(bet.stake) : state.casino.stake;
      state.casino.bet = {
        type: bet.type || null,
        value: bet.value ?? null,
        stake,
      };
    }
    saveCasinoState();
  };

  TerminalApp.getCasinoBet = () => (state.casino.bet ? { ...state.casino.bet } : null);

  TerminalApp.clearCasinoBet = () => {
    state.casino.bet = { type: null, value: null, stake: state.casino.stake };
    saveCasinoState();
  };

  TerminalApp.setCasinoAwaitingAge = (flag, mode = null) => {
    state.casino.awaitingAge = Boolean(flag);
    if (flag && mode) {
      state.casino.pendingMode = mode;
    } else if (!state.casino.awaitingReplay && !flag) {
      state.casino.pendingMode = mode ? mode : state.casino.pendingMode;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingAge = () => state.casino.awaitingAge;

  TerminalApp.setCasinoAwaitingReplay = (flag, mode = null) => {
    state.casino.awaitingReplay = Boolean(flag);
    if (flag && mode) {
      state.casino.pendingMode = mode;
    } else if (!state.casino.awaitingAge && !flag) {
      state.casino.pendingMode = null;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingReplay = () => state.casino.awaitingReplay;

  TerminalApp.setCasinoAwaitingSpin = (flag, mode = null) => {
    state.casino.awaitingSpin = Boolean(flag);
    if (flag && mode) {
      state.casino.pendingMode = mode;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingSpin = () => state.casino.awaitingSpin;

  TerminalApp.setCasinoAwaitingMode = (flag) => {
    state.casino.awaitingMode = Boolean(flag);
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingMode = () => state.casino.awaitingMode;

  TerminalApp.clearCasinoPendingMode = () => {
    state.casino.pendingMode = null;
    saveCasinoState();
  };

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
