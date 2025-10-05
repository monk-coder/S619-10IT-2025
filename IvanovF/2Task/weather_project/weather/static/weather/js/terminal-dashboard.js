const output = document.getElementById("output");
const input = document.getElementById("cmdline");
const clockEl = document.getElementById("clock");
const cursorEl = document.querySelector('.cursor');
const measureEl = document.getElementById('caret-measure');
const promptLabel = document.getElementById('prompt-label');
const historyList = document.getElementById('history-list');

let notes = JSON.parse(localStorage.getItem('terminal_notes') || '[]');
let timezoneOffset = parseFloat(localStorage.getItem('terminal_tz') || '0') || 0;
let timerInterval = null;
let currentUser = 'guest';

let serverUtcMillis = null;
let syncPerfNow = null;

function updateCursorPosition() {
  if (!cursorEl || !measureEl) return;
  const value = input.value || '';
  const caretIndex = input.selectionStart ?? value.length;
  const beforeCaret = value.slice(0, caretIndex).replace(/ /g, '\u00a0') || '\u200b';
  measureEl.textContent = beforeCaret;
  const caretLeft = measureEl.offsetWidth - input.scrollLeft;
  cursorEl.style.left = `${Math.max(0, caretLeft)}px`;
}

function updatePrompt() {
  const userLabel = currentUser || 'guest';
  promptLabel.textContent = `${userLabel}@dash:~$`;
}

['input', 'keyup', 'click', 'focus', 'mouseup'].forEach(evt => {
  input.addEventListener(evt, () => requestAnimationFrame(updateCursorPosition));
});
window.addEventListener('resize', () => requestAnimationFrame(updateCursorPosition));

function print(text, cls = "") {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.textContent = text;
  output.appendChild(div);
  output.scrollTop = output.scrollHeight;
}
function printHtml(html, cls = "") {
  const div = document.createElement("div");
  if (cls) div.className = cls;
  div.innerHTML = html;
  output.appendChild(div);
  output.scrollTop = output.scrollHeight;
}
function pad2(n) { return String(n).padStart(2, '0'); }

const helpItems = [
  'help',
  'login <логин> <пароль>',
  'signup <логин> <пароль>',
  'weather <city>',
  'flight <IATA>',
  'note <text>',
  'notes',
  'timer <seconds>',
  'timezone <offset>',
  'clear'
];
const commandsList = Array.from(new Set(helpItems.map(item => item.split(' ')[0])));
const commandsWithArgs = new Set(['login', 'signup', 'weather', 'flight', 'note', 'timer', 'timezone']);

function showHelp() {
  print('Welcome to Terminal Dashboard');
  printHtml('<span class="big">Terminal Dashboard</span>');
  print('Available commands:');
  helpItems.forEach(entry => print(`- ${entry}`));
  print('(Часы синхронизируются с реальным UTC временем через backend API.)');
}

function autocompleteCommand() {
  const value = input.value;
  const caretIndex = input.selectionStart ?? value.length;
  const beforeCaret = value.slice(0, caretIndex);
  if (beforeCaret.includes(' ')) return;
  const partial = beforeCaret.trim();
  if (!partial) return;
  const matches = commandsList.filter(cmd => cmd.startsWith(partial));
  if (matches.length === 0) return;
  if (matches.length === 1) {
    const base = matches[0];
    const suffix = commandsWithArgs.has(base) ? ' ' : '';
    const completed = base + suffix;
    const rest = value.slice(caretIndex);
    input.value = completed + rest;
    const pos = completed.length;
    input.setSelectionRange(pos, pos);
    requestAnimationFrame(updateCursorPosition);
  } else {
    print(`Suggestions: ${matches.join('  ')}`);
  }
}

function formatHistoryTime(timestamp) {
  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) return '';
  return date.toLocaleString(undefined, {
    day: '2-digit',
    month: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function renderHistory(entries) {
  if (!historyList) return;
  historyList.innerHTML = '';

  if (currentUser === 'guest') {
    const info = document.createElement('div');
    info.className = 'history-empty';
    info.textContent = 'Войдите, чтобы видеть историю запросов.';
    historyList.appendChild(info);
    return;
  }

  if (!entries || entries.length === 0) {
    const info = document.createElement('div');
    info.className = 'history-empty';
    info.textContent = 'История пока пуста.';
    historyList.appendChild(info);
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
    time.textContent = formatHistoryTime(entry.created_at);
    item.appendChild(city);
    if (time.textContent) item.appendChild(time);
    historyList.appendChild(item);
  });
}

async function fetchHistory() {
  if (!historyList) return;
  if (currentUser === 'guest') {
    renderHistory([]);
    return;
  }

  try {
    const resp = await fetch('/api/history/', { credentials: 'same-origin' });
    if (!resp.ok) throw new Error('history request failed');
    const data = await resp.json();
    const entries = Array.isArray(data.entries) ? data.entries : [];
    renderHistory(entries);
  } catch (err) {
    renderHistory([]);
  }
}

async function syncAuthStatus() {
  try {
    const resp = await fetch('/api/auth/status/', { credentials: 'same-origin' });
    if (!resp.ok) throw new Error('status request failed');
    const data = await resp.json();
    if (data.authenticated && data.username) {
      currentUser = data.username;
    } else {
      currentUser = 'guest';
    }
  } catch (err) {
    currentUser = 'guest';
  }
  updatePrompt();
  await fetchHistory();
}

async function executeCommand(raw) {
  const parts = raw.split(/\s+/).filter(Boolean);
  if (parts.length === 0) return;
  const cmd = parts[0].toLowerCase();
  const arg = parts.slice(1).join(' ');

  if (cmd === 'help') { showHelp(); return; }
  if (cmd === 'clear') { output.innerHTML = ''; return; }

  if (cmd === 'signup') {
    const [username, password] = (arg || '').split(/\s+/);
    if (!username || !password) { print('Error: используйте signup <логин> <пароль>', 'error'); return; }
    print(`Создание аккаунта ${username}...`);
    try {
      const resp = await fetch('/api/auth/register/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, password }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) { print(`Error: ${data.error || resp.statusText}`, 'error'); return; }
      currentUser = data.username || username;
      updatePrompt();
      print(data.message || 'Регистрация завершена');
      await fetchHistory();
    } catch (err) {
      print(`Error: ${err.message}`, 'error');
    }
    return;
  }

  if (cmd === 'login') {
    const [username, password] = (arg || '').split(/\s+/);
    if (!username || !password) { print('Error: используйте login <логин> <пароль>', 'error'); return; }
    print(`Авторизация ${username}...`);
    try {
      const resp = await fetch('/api/auth/login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify({ username, password }),
      });
      const data = await resp.json();
      if (!resp.ok || data.error) { print(`Error: ${data.error || resp.statusText}`, 'error'); return; }
      currentUser = data.username || username;
      updatePrompt();
      print(data.message || 'Авторизация успешна');
      await fetchHistory();
    } catch (err) {
      print(`Error: ${err.message}`, 'error');
    }
    return;
  }

  if (cmd === 'timezone') {
    if (!arg) { print('Error: provide offset, e.g. timezone +3 or timezone -5.5', 'error'); return; }
    const val = parseFloat(arg);
    if (!isFinite(val)) { print('Error: invalid offset', 'error'); return; }
    timezoneOffset = val;
    localStorage.setItem('terminal_tz', String(timezoneOffset));
    updateClockDisplay();
    print(`Timezone set to UTC${timezoneOffset >= 0 ? '+' : ''}${timezoneOffset}`);
    return;
  }

  if (cmd === 'note') {
    if (!arg) { print('Error: note text required', 'error'); return; }
    notes.push(arg);
    localStorage.setItem('terminal_notes', JSON.stringify(notes));
    print(`Note saved (#${notes.length})`);
    return;
  }

  if (cmd === 'notes') {
    if (notes.length === 0) { print('No notes yet.'); return; }
    print('Notes:');
    notes.forEach((n, i) => print(`${i + 1}. ${n}`));
    return;
  }

  if (cmd === 'timer') {
    if (!arg || isNaN(arg)) { print('Error: seconds required', 'error'); return; }
    let sec = Math.max(0, Math.floor(Number(arg)));
    if (timerInterval) { clearInterval(timerInterval); timerInterval = null; }
    print(`Timer started: ${sec} seconds`);
    timerInterval = setInterval(() => {
      if (sec <= 0) {
        clearInterval(timerInterval);
        timerInterval = null;
        print('⏰ Timer finished!', 'big');
      } else {
        print(`... ${sec} sec left`);
        sec--;
      }
    }, 1000);
    return;
  }
  if (cmd === 'logout') {
    if (currentUser === 'guest') {
      print('Вы не вошли в систему.');
      return;
    }
    print(`Выход из аккаунта ${currentUser}...`);
    try {
      const resp = await fetch('/api/auth/logout/', {
        method: 'POST',
        credentials: 'same-origin'
      });
      const data = await resp.json();
      if (!resp.ok || data.error) {
        print(`Error: ${data.error || resp.statusText}`, 'error');
        return;
      }
      currentUser = 'guest';
      updatePrompt();
      print(data.message || 'Вы вышли из системы.');
      await fetchHistory();
    } catch (err) {
      print(`Error: ${err.message}`, 'error');
    }
    return;
  }


  if (cmd === 'weather') {
    if (!arg) { print('Error: city required', 'error'); return; }
    print(`Fetching weather for ${arg}...`);
    try {
      const resp = await fetch(`/api/weather/?city=${encodeURIComponent(arg)}`);
      const data = await resp.json();
      if (!resp.ok || data.error) { print(`Error: ${data.error || resp.statusText}`, 'error'); return; }
      const dsc = (data.description || '').toLowerCase();
      let icon = asciiIcons.sun;
      if (dsc.includes('дожд')) icon = asciiIcons.rain;
      else if (dsc.includes('снег')) icon = asciiIcons.snow;
      else if (dsc.includes('облач')) icon = asciiIcons.cloud;
      printHtml(`<pre style="margin:0;color:#0f0;">${icon}</pre>`);
      print(`${(data.city || '').toUpperCase()}`, 'big');
      print(`Температура: ${data.temperature}°C`);
      print(`Влажность: ${data.humidity}%`);
      print(`Описание: ${data.description}`);
      if (currentUser !== 'guest') fetchHistory();
    } catch (err) {
      print(`Error: ${err.message}`, 'error');
    }
    return;
  }

  if (cmd === 'flight') {
    if (!arg) { print('Error: airport IATA required', 'error'); return; }
    print(`Fetching flight for ${arg.toUpperCase()}...`);
    try {
      const resp = await fetch(`/api/flight/?airport=${encodeURIComponent(arg)}`);
      const data = await resp.json();
      if (!resp.ok || data.error) { print(`Error: ${data.error || resp.statusText}`, 'error'); return; }
      printHtml(`<pre style="margin:0;color:#0f0;">${asciiIcons.plane}</pre>`);
      print(`Рейс: ${data.flight_number}`, 'big');
      print(`Авиакомпания: ${data.airline}`);
      print(`Статус: ${data.status}`);
      print(`Вылет: ${data.departure_airport} @ ${data.departure_time || 'N/A'}`);
      print(`Прилет: ${data.arrival_airport} @ ${data.arrival_time || 'N/A'}`);
    } catch (err) {
      print(`Error: ${err.message}`, 'error');
    }
    return;
  }

  print(`Unknown command: ${cmd}`, 'error');
}

async function syncTime() {
  try {
    const res = await fetch('/api/time/');
    const data = await res.json();
    if (data.error) throw new Error(data.error);
    if (typeof data.unixtime === 'number') serverUtcMillis = data.unixtime * 1000;
    else if (data.utc_datetime) serverUtcMillis = Date.parse(data.utc_datetime);
    else serverUtcMillis = Date.now() + (new Date().getTimezoneOffset() * 60000);
    syncPerfNow = performance.now();
    updateClockDisplay();
  } catch (err) {
    serverUtcMillis = Date.now() + (new Date().getTimezoneOffset() * 60000);
    syncPerfNow = performance.now();
    updateClockDisplay();
  }
}
function getCurrentUtcMillis() {
  if (serverUtcMillis === null || syncPerfNow === null) return Date.now() + (new Date().getTimezoneOffset() * 60000);
  return serverUtcMillis + (performance.now() - syncPerfNow);
}
function updateClockDisplay() {
  const utcMillis = getCurrentUtcMillis();
  const tzMillis = utcMillis + timezoneOffset * 3600000;
  const d = new Date(tzMillis);
  const Y = d.getUTCFullYear();
  const M = pad2(d.getUTCMonth() + 1);
  const D = pad2(d.getUTCDate());
  const h = pad2(d.getUTCHours());
  const m = pad2(d.getUTCMinutes());
  const s = pad2(d.getUTCSeconds());
  const sign = timezoneOffset >= 0 ? '+' : '';
  clockEl.textContent = `UTC${sign}${timezoneOffset} ${Y}-${M}-${D} ${h}:${m}:${s}`;
}

setInterval(() => { updateClockDisplay(); }, 1000);
setInterval(() => { syncTime(); }, 5 * 60 * 1000);
syncTime();

const asciiIcons = {
  sun: `  \\   /  \n   .-.   \n- (   ) -\n   \`-’   \n  /   \\  `,
  cloud: `    .--.   \n .-(    ). \n(___.__)__)`,
  rain: `    .--.   \n .-(    ). \n(___.__)__)\n ' ' ' ' ' `,
  snow: `    .--.   \n .-(    ). \n(___.__)__)\n  *  *  *  `,
  plane: `     __|__\n--@--@--(_)--@--@--`
};

input.addEventListener('keydown', async (e) => {
  if (e.key === 'Tab') {
    e.preventDefault();
    autocompleteCommand();
    requestAnimationFrame(updateCursorPosition);
    return;
  }
  if (e.key === 'Enter') {
    e.preventDefault();
    const raw = input.value.trim();
    input.value = '';
    requestAnimationFrame(updateCursorPosition);
    if (!raw) return;
    print(`${currentUser}@dash:~$ ${raw}`);
    try { await executeCommand(raw); } catch (err) { print(`Command error: ${err.message || err}`, 'error'); }
    return;
  }
  requestAnimationFrame(updateCursorPosition);
});

(function restoreState() {
  try { notes = JSON.parse(localStorage.getItem('terminal_notes') || '[]'); } catch (e) { notes = []; }
  timezoneOffset = parseFloat(localStorage.getItem('terminal_tz') || '0') || 0;
})();
updatePrompt();
renderHistory([]);
print("Введите 'help' для списка команд.");
requestAnimationFrame(updateCursorPosition);
syncAuthStatus();
