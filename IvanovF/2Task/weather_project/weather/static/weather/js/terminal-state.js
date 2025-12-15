// Этот файл просто хранит состояние терминала и даёт к нему доступ.
(function () {
  var TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  // Один раз находим важные DOM-элементы, чтобы не обращаться к document каждый раз.
  var elements = {
    output: document.getElementById('output'),
    input: document.getElementById('cmdline'),
    hint: document.getElementById('cmdline-hint'),
    clock: document.getElementById('clock'),
    cursor: document.querySelector('.cursor'),
    measure: document.getElementById('caret-measure'),
    promptLabel: document.getElementById('prompt-label'),
    historyList: document.getElementById('history-list')
  };

  TerminalApp.elements = elements;

  var CASINO_STORAGE_KEY = 'terminal_casino_state';
  var CASINO_DEFAULT_BALANCE = 100;
  var CASINO_DEFAULT_STAKE = 10;

  // Стартовое состояние всего приложения.
  // По сути это «source of truth» для заметок, задач, авторизации и казино.
  var state = {
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
      bet: { type: null, value: null, stake: CASINO_DEFAULT_STAKE }
    }
  };

  TerminalApp.state = state;

  // Восстанавливаем данные из localStorage.
  // Каждую секцию оборачиваем в try/catch, чтобы не упасть из-за битых данных.
  TerminalApp.restoreState = function () {
    try {
      var savedNotes = JSON.parse(localStorage.getItem('terminal_notes') || '[]');
      state.notes = Array.isArray(savedNotes) ? savedNotes : [];
    } catch (err) {
      state.notes = [];
    }

    try {
      var storedCasino = JSON.parse(localStorage.getItem(CASINO_STORAGE_KEY) || '{}');
      if (storedCasino && typeof storedCasino === 'object') {
        var initial = Number(storedCasino.initialBalance);
        var balance = Number(storedCasino.balance);
        var stake = Number(storedCasino.stake);
        state.casino.initialBalance = Number.isFinite(initial) && initial > 0 ? Math.floor(initial) : CASINO_DEFAULT_BALANCE;
        state.casino.balance = Number.isFinite(balance) && balance >= 0 ? Math.floor(balance) : state.casino.initialBalance;
        state.casino.ageConfirmed = !!storedCasino.ageConfirmed;
        var storedAge = Number(storedCasino.ageValue);
        state.casino.ageValue = Number.isFinite(storedAge) && storedAge > 0 ? Math.floor(storedAge) : null;
        state.casino.awaitingAge = !!storedCasino.awaitingAge;
        state.casino.awaitingReplay = !!storedCasino.awaitingReplay;
        state.casino.awaitingSpin = !!storedCasino.awaitingSpin;
        state.casino.awaitingMode = !!storedCasino.awaitingMode;
        state.casino.pendingMode = storedCasino.pendingMode || null;
        state.casino.lastMode = storedCasino.lastMode || 'roulette';
        state.casino.stake = Number.isFinite(stake) && stake > 0 ? Math.floor(stake) : CASINO_DEFAULT_STAKE;
        if (storedCasino.bet && typeof storedCasino.bet === 'object') {
          var betStake = Number(storedCasino.bet.stake);
          state.casino.bet = {
            type: storedCasino.bet.type || null,
            value: typeof storedCasino.bet.value !== 'undefined' ? storedCasino.bet.value : null,
            stake: Number.isFinite(betStake) && betStake > 0 ? Math.floor(betStake) : state.casino.stake
          };
        }
      }
    } catch (err) {
      state.casino = {
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
        bet: { type: null, value: null, stake: CASINO_DEFAULT_STAKE }
      };
    }

    // Дополнительная защита от мусорных значений.
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

    var storedTz = localStorage.getItem('terminal_tz');
    if (storedTz === null) {
      var deviceOffset = -new Date().getTimezoneOffset() / 60;
      state.timezoneOffset = deviceOffset;
      localStorage.setItem('terminal_tz', String(deviceOffset));
    } else {
      state.timezoneOffset = parseFloat(storedTz) || 0;
    }
  };

  // Блок задач и заметок.
  TerminalApp.setTasks = function (tasks) {
    // Кладём копию массива, чтобы не зависеть от внешних мутаций.
    state.tasks = Array.isArray(tasks) ? tasks.slice() : [];
  };

  TerminalApp.getTasks = function () {
    // Возвращаем копию, вызывающий код не должен менять state.tasks напрямую.
    return state.tasks.slice();
  };

  TerminalApp.upsertTask = function (task) {
    if (!task || typeof task.id !== 'number') {
      return;
    }
    // Если задача с таким id уже есть — заменяем, иначе добавляем в начало списка.
    var index = state.tasks.findIndex(function (item) { return item.id === task.id; });
    if (index === -1) {
      state.tasks.unshift(task);
    } else {
      state.tasks[index] = task;
    }
  };

  TerminalApp.removeTask = function (taskId) {
    // Фильтруем список задач, оставляя все кроме указанной.
    state.tasks = state.tasks.filter(function (item) {
      return item.id !== taskId;
    });
  };

  TerminalApp.describeTask = function (task) {
    if (!task) {
      return '';
    }
    // Форматируем строку вида [id] Город: текст @ дата.
    var created = task.created_at ? ' @ ' + TerminalApp.formatHistoryTime(task.created_at) : '';
    return '[' + task.id + '] ' + task.city + ': ' + task.text + created;
  };

  TerminalApp.setCurrencySession = function (session) {
    state.currencySession = session;
  };

  TerminalApp.getCurrencySession = function () {
    return state.currencySession;
  };

  TerminalApp.clearCurrencySession = function () {
    state.currencySession = null;
  };

  TerminalApp.saveNotes = function () {
    localStorage.setItem('terminal_notes', JSON.stringify(state.notes));
  };

  TerminalApp.addNote = function (note) {
    // Добавляем заметку и сразу же сохраняем обновлённый массив в localStorage.
    state.notes.push(note);
    TerminalApp.saveNotes();
  };

  TerminalApp.getNotes = function () {
    // Возвращаем копию списка заметок.
    return state.notes.slice();
  };

  // Время и таймеры.
  TerminalApp.setTimezoneOffset = function (value) {
    state.timezoneOffset = value;
    localStorage.setItem('terminal_tz', String(value));
  };

  TerminalApp.getTimezoneOffset = function () {
    return state.timezoneOffset;
  };

  TerminalApp.setTimerInterval = function (interval) {
    if (state.timerInterval) {
      // Гарантируем, что параллельно не будет работать несколько таймеров.
      clearInterval(state.timerInterval);
    }
    state.timerInterval = interval;
  };

  TerminalApp.clearTimerInterval = function () {
    if (state.timerInterval) {
      clearInterval(state.timerInterval);
      state.timerInterval = null;
    }
  };

  // Информация о пользователе.
  TerminalApp.getCurrentUser = function () {
    return state.currentUser;
  };

  TerminalApp.setCurrentUser = function (user) {
    // Пустое значение трактуем как гостя.
    state.currentUser = user || 'guest';
  };

  TerminalApp.setServerTimeRef = function (serverMillis, perfNow) {
    // Запоминаем опорное UTC-время сервера и момент синхронизации по performance.now().
    state.serverUtcMillis = serverMillis;
    state.syncPerfNow = perfNow;
  };

  TerminalApp.getServerTimeRef = function () {
    return {
      serverUtcMillis: state.serverUtcMillis,
      syncPerfNow: state.syncPerfNow
    };
  };

  TerminalApp.pad2 = function (n) {
    return String(n).padStart(2, '0');
  };

  // Работа с казино хранится в отдельном блоке.
  function saveCasinoState() {
    try {
      localStorage.setItem(CASINO_STORAGE_KEY, JSON.stringify(state.casino));
    } catch (err) {
      // просто пропускаем
    }
  }

  TerminalApp.getCasinoState = function () {
    // Возвращаем клон, чтобы внешний код не мог мутировать оригинал напрямую.
    return JSON.parse(JSON.stringify(state.casino));
  };

  TerminalApp.adjustCasinoBalance = function (delta) {
    var next = Math.max(0, Math.floor(state.casino.balance + delta));
    state.casino.balance = next;
    saveCasinoState();
    return next;
  };

  TerminalApp.resetCasinoBalance = function () {
    state.casino.balance = state.casino.initialBalance;
    saveCasinoState();
    return state.casino.balance;
  };

  TerminalApp.setCasinoInitialBalance = function (value) {
    if (Number.isFinite(value) && value > 0) {
      state.casino.initialBalance = Math.floor(value);
      if (state.casino.balance > state.casino.initialBalance) {
        // Если текущий баланс выше нового максимума, обрезаем его.
        state.casino.balance = state.casino.initialBalance;
      }
      saveCasinoState();
    }
  };

  TerminalApp.getCasinoStake = function () {
    return state.casino.stake;
  };

  TerminalApp.setCasinoStake = function (value) {
    if (Number.isFinite(value) && value > 0) {
      state.casino.stake = Math.floor(value);
      if (!state.casino.bet) {
        state.casino.bet = { type: null, value: null, stake: state.casino.stake };
      } else {
        // Ставка хранится также внутри текущей ставки рулетки/слотов.
        state.casino.bet.stake = state.casino.stake;
      }
      saveCasinoState();
    }
  };

  function clampCasinoAge(value) {
    if (!Number.isFinite(value)) {
      return null;
    }
    var normalized = Math.floor(value);
    if (normalized <= 0) {
      return null;
    }
    return Math.min(normalized, 120);
  }

  TerminalApp.confirmCasinoAge = function (ageValue) {
    state.casino.ageConfirmed = true;
    state.casino.ageValue = clampCasinoAge(ageValue);
    saveCasinoState();
  };

  TerminalApp.revokeCasinoAge = function () {
    state.casino.ageConfirmed = false;
    state.casino.ageValue = null;
    saveCasinoState();
  };

  TerminalApp.getCasinoAgeValue = function () {
    return Number.isFinite(state.casino.ageValue) ? state.casino.ageValue : null;
  };

  TerminalApp.isCasinoAgeConfirmed = function () {
    return state.casino.ageConfirmed;
  };

  TerminalApp.setCasinoPendingMode = function (mode) {
    state.casino.pendingMode = mode || null;
    saveCasinoState();
  };

  TerminalApp.getCasinoPendingMode = function () {
    return state.casino.pendingMode;
  };

  TerminalApp.setCasinoLastMode = function (mode) {
    if (mode) {
      state.casino.lastMode = mode;
    }
  };

  TerminalApp.getCasinoLastMode = function () {
    return state.casino.lastMode || 'roulette';
  };

  TerminalApp.setCasinoBet = function (bet) {
    if (!bet || typeof bet !== 'object') {
      state.casino.bet = { type: null, value: null, stake: state.casino.stake };
    } else {
      var betStake = Number.isFinite(bet.stake) && bet.stake > 0 ? Math.floor(bet.stake) : state.casino.stake;
      state.casino.bet = {
        type: bet.type || null,
        value: typeof bet.value !== 'undefined' ? bet.value : null,
        stake: betStake
      };
    }
    saveCasinoState();
  };

  TerminalApp.getCasinoBet = function () {
    // Возвращаем копию, чтобы посторонний код не мог изменять объект напрямую.
    return state.casino.bet ? JSON.parse(JSON.stringify(state.casino.bet)) : null;
  };

  TerminalApp.clearCasinoBet = function () {
    state.casino.bet = { type: null, value: null, stake: state.casino.stake };
    saveCasinoState();
  };

  TerminalApp.setCasinoAwaitingAge = function (flag, mode) {
    state.casino.awaitingAge = !!flag;
    if (flag && mode) {
      // Если ожидаем ввод возраста, запоминаем, какую игру хотели запустить.
      state.casino.pendingMode = mode;
    } else if (!state.casino.awaitingReplay && !flag) {
      state.casino.pendingMode = mode ? mode : state.casino.pendingMode;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingAge = function () {
    return state.casino.awaitingAge;
  };

  TerminalApp.setCasinoAwaitingReplay = function (flag, mode) {
    state.casino.awaitingReplay = !!flag;
    if (flag && mode) {
      state.casino.pendingMode = mode;
    } else if (!state.casino.awaitingAge && !flag) {
      state.casino.pendingMode = null;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingReplay = function () {
    return state.casino.awaitingReplay;
  };

  TerminalApp.setCasinoAwaitingSpin = function (flag, mode) {
    state.casino.awaitingSpin = !!flag;
    if (flag && mode) {
      state.casino.pendingMode = mode;
    }
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingSpin = function () {
    return state.casino.awaitingSpin;
  };

  TerminalApp.setCasinoAwaitingMode = function (flag) {
    state.casino.awaitingMode = !!flag;
    saveCasinoState();
  };

  TerminalApp.isCasinoAwaitingMode = function () {
    return state.casino.awaitingMode;
  };

  TerminalApp.clearCasinoPendingMode = function () {
    state.casino.pendingMode = null;
    saveCasinoState();
  };

  // Остальные функции помогают обновлять интерфейс.
  TerminalApp.updateCursorPosition = function () {
    var input = elements.input;
    var cursor = elements.cursor;
    var measure = elements.measure;
    if (!input || !cursor || !measure) {
      return;
    }
    var value = input.value || '';
    var caretIndex = input.selectionStart != null ? input.selectionStart : value.length;
    // Заменяем пробелы на неразрывные, чтобы измерить ширину текста до каретки.
    var beforeCaret = value.slice(0, caretIndex).replace(/ /g, '\u00a0') || '\u200b';
    measure.textContent = beforeCaret;
    var caretLeft = measure.offsetWidth - input.scrollLeft;
    cursor.style.left = Math.max(0, caretLeft) + 'px';
  };

  TerminalApp.updatePrompt = function () {
    if (!elements.promptLabel) {
      return;
    }
    var userLabel = TerminalApp.getCurrentUser() || 'guest';
    // Отрисовываем приглашение в духе shell: <user>@dash:~$
    elements.promptLabel.textContent = userLabel + '@dash:~$';
  };

  TerminalApp.print = function (text, cls) {
    if (!elements.output) {
      return;
    }
    var div = document.createElement('div');
    if (cls) {
      div.className = cls;
    }
    div.textContent = text;
    elements.output.appendChild(div);
    // Следим, чтобы после добавления строки окно скроллилось вниз.
    elements.output.scrollTop = elements.output.scrollHeight;
  };

  TerminalApp.printHtml = function (html, cls) {
    if (!elements.output) {
      return;
    }
    var div = document.createElement('div');
    if (cls) {
      div.className = cls;
    }
    div.innerHTML = html;
    elements.output.appendChild(div);
    elements.output.scrollTop = elements.output.scrollHeight;
  };

  TerminalApp.formatHistoryTime = function (timestamp) {
    var date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) {
      return '';
    }
    return date.toLocaleString(undefined, {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  TerminalApp.renderHistory = function (entries) {
    var list = elements.historyList;
    if (!list) {
      return;
    }
    list.innerHTML = '';

    if (TerminalApp.getCurrentUser() === 'guest') {
      // Для гостей показываем подсказку авторизоваться.
      var infoGuest = document.createElement('div');
      infoGuest.className = 'history-empty';
      infoGuest.textContent = 'Войдите, чтобы видеть историю запросов.';
      list.appendChild(infoGuest);
      return;
    }

    if (!entries || !entries.length) {
      // Авторизованный пользователь, но история пуста.
      var infoEmpty = document.createElement('div');
      infoEmpty.className = 'history-empty';
      infoEmpty.textContent = 'История пока пуста.';
      list.appendChild(infoEmpty);
      return;
    }

    entries.forEach(function (entry) {
      var item = document.createElement('div');
      item.className = 'history-item';

      var city = document.createElement('div');
      city.className = 'history-item-city';
      city.textContent = entry.city;

      var time = document.createElement('div');
      time.className = 'history-item-time';
      time.textContent = TerminalApp.formatHistoryTime(entry.created_at);

      item.appendChild(city);
      if (time.textContent) {
        item.appendChild(time);
      }
      list.appendChild(item);
    });
  };

  TerminalApp.updateClockDisplay = function () {
    if (!elements.clock) {
      return;
    }
    var timezoneOffset = TerminalApp.getTimezoneOffset();
    var sign = timezoneOffset >= 0 ? '+' : '';
    var utcMillis = TerminalApp.getCurrentUtcMillis ? TerminalApp.getCurrentUtcMillis() : Date.now();
    var tzMillis = utcMillis + timezoneOffset * 3600000;
    var date = new Date(tzMillis);
    var Y = date.getUTCFullYear();
    var M = TerminalApp.pad2(date.getUTCMonth() + 1);
    var D = TerminalApp.pad2(date.getUTCDate());
    var h = TerminalApp.pad2(date.getUTCHours());
    var m = TerminalApp.pad2(date.getUTCMinutes());
    var s = TerminalApp.pad2(date.getUTCSeconds());
    // Формат ANSI: UTC±X YYYY-MM-DD HH:MM:SS.
    elements.clock.textContent = 'UTC' + sign + timezoneOffset + ' ' + Y + '-' + M + '-' + D + ' ' + h + ':' + m + ':' + s;
  };
})();
