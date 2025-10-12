(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const helpItems = [
    'help — показать список команд',
    'admin — админ-панель (staff)',
    'casino — азартные игры (18+, рулетка и слоты)',
    'fetch — вывести информацию о системе',
    'login <логин> <пароль> — войти в аккаунт',
    'signup <логин> <пароль> — зарегистрироваться',
    'logout — выйти из аккаунта',
    'weather <город> — узнать погоду',
    'flight <IATA> — статус рейса',
    'currency <из> [в] [сумма] — конвертация валют из списка (например: currency usd rub 100)',
    'taskadd <город>|<текст> — сохранить напоминание по погоде',
    'tasks — показать сохранённые напоминания',
    'taskupdate <id>|[город]|[текст] — изменить напоминание',
    'taskdelete <id> — удалить напоминание',
    'note <текст> — добавить локальную заметку',
    'notes — показать локальные заметки',
    'timer <секунды> — запустить таймер',
    'timezone <смещение> — сменить пояс, например timezone +3',
    'clear — очистить экран',
  ];

  const commandsList = Array.from(new Set(helpItems.map((item) => item.split(' ')[0])));
  const commandsWithArgs = new Set(['login', 'signup', 'weather', 'flight', 'currency', 'note', 'taskadd', 'taskupdate', 'taskdelete', 'timer', 'timezone', 'casino']);

  const asciiIcons = {
    sun: '  \\   /  \n   .-.   \n- (   ) -\n   `-’   \n  /   \\  ',
    cloud: '    .--.   \n .-(    ). \n(___.__)__)',
    rain: "    .--.   \n .-(    ). \n(___.__)__)\n ' ' ' ' ' ",
    snow: '    .--.   \n .-(    ). \n(___.__)__)\n  *  *  *  ',
    plane: '     __|__\n--@--@--(_)--@--@--',
    arch: [
      '                 /#\\',
      '                /###\\',
      '               /#####\\',
      '              /#######\\',
      '             _ "=######\\',
      '            /##=,_\\#####\\',
      '           /#############\\',
      '          /###############\\',
      '         /#################\\',
      '        /###################\\',
      '       /########*"""*########\\',
      '      /#######/       \\#######\\',
      '     /########         ########\\',
      '    /#########         ######m=,_',
      '   /##########         ##########\\',
      '  /######***             ***######\\',
      ' /###**                       **###\\',
      '/**                               **\\',
    ].join('\n'),
  };

  TerminalApp.helpItems = helpItems;
  TerminalApp.asciiIcons = asciiIcons;

  const CASINO_CONFIG = Object.freeze({
    spinCost: 10,
    pairPayout: 20,
    jackpotPayout: 60,
    frames: 6,
    frameDelay: 140,
    frameDelayStep: 40,
  });

  TerminalApp.CASINO_CONFIG = CASINO_CONFIG;

  const isYesResponse = (value) => {
    const entry = (value || '').trim().toLowerCase();
    return ['y', 'yes', 'yeah', 'да', 'д', 'угу', 'ага'].includes(entry);
  };

  const isNoResponse = (value) => {
    const entry = (value || '').trim().toLowerCase();
    return ['n', 'no', 'нет', 'н', 'неа'].includes(entry);
  };

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const randomDigit = () => Math.floor(Math.random() * 10);
  const createSlotDigits = () => Array.from({ length: 3 }, randomDigit);
  const formatSlotDigit = (value) => String(value).slice(-1);
  const renderSlotMachine = (digits, balance, stake, message = '') => {
    const cells = digits.map((digit) => formatSlotDigit(digit));
    const rows = [
      '╔════════════════════╗',
      '║    SLOT MACHINE    ║',
      '║ ╔════╦════╦════╗   ║',
      `║ ║  ${cells[0]} ║  ${cells[1]} ║  ${cells[2]} ║   ║`,
      '║ ╚════╩════╩════╝   ║',
      '╠════════════════════╣',
      `║ Баланс: ${String(balance).padEnd(6, ' ')}║`,
      `║ Ставка:  ${String(stake).padEnd(6, ' ')}║`,
      '╚════════════════════╝',
    ];
    if (message) rows.push(message);
    return rows.join('\n');
  };

  const rouletteColor = (number) => {
    if (number === 0) return { label: 'зелёный', short: 'GRN' };
    return number % 2 === 0 ? { label: 'красный', short: 'RED' } : { label: 'чёрный', short: 'BLK' };
  };

  const renderRouletteFrame = (number, balance, stake, message = '') => {
    const numLabel = String(number).padStart(2, ' ');
    const color = rouletteColor(number);
    const rows = [
      '┌──────────────┐',
      '│   РУЛЕТКА    │',
      '├──────────────┤',
      `│   ${numLabel}  ${color.short.padEnd(3, ' ')} │`,
      '└──────────────┘',
      `Баланс: ${balance}  |  Ставка: ${stake}`,
    ];
    if (message) rows.push(message);
    return rows.join('\n');
  };

  const colorAliases = {
    red: 'red',
    красный: 'red',
    красная: 'red',
    r: 'red',
    black: 'black',
    чёрный: 'black',
    черный: 'black',
    b: 'black',
    green: 'green',
    зелёный: 'green',
    зеленый: 'green',
    g: 'green',
  };

  const parityAliases = {
    odd: 'odd',
    нечет: 'odd',
    нечёт: 'odd',
    o: 'odd',
    even: 'even',
    чет: 'even',
    чёт: 'even',
    e: 'even',
  };

  const colorNames = {
    red: 'красный',
    black: 'чёрный',
    green: 'зелёный',
  };

  const describeRouletteBet = (bet) => {
    if (!bet || !bet.type) return 'чётное число';
    switch (bet.type) {
      case 'number':
        return `число ${bet.value}`;
      case 'color':
        return `цвет ${colorNames[bet.value] || bet.value}`;
      case 'parity':
        return bet.value === 'even' ? 'чётное' : 'нечётное';
      default:
        return 'чётное число';
    }
  };

  const buildSpinPrompt = (mode, stake, bet) => {
    if (mode === 'slots') {
      return `Запустить слот-машину со ставкой ${stake}? (y/n, q — выход)`;
    }
    const betDescription = describeRouletteBet(bet);
    return `Ставка на рулетку: ${betDescription}, сумма ${stake}. Крутить колесо? (y/n, q — выход)`;
  };

  const parseStakeTokens = (tokens, defaultStake) => {
    let stake = defaultStake;
    const remaining = [];
    for (let i = 0; i < tokens.length; i += 1) {
      const token = tokens[i];
      const lower = token.toLowerCase();
      if (lower === 'stake' && tokens[i + 1]) {
        const value = Number(tokens[i + 1]);
        if (Number.isFinite(value) && value > 0) {
          stake = Math.floor(value);
        }
        i += 1;
        continue;
      }
      if (lower.startsWith('stake=')) {
        const value = Number(lower.split('=')[1]);
        if (Number.isFinite(value) && value > 0) {
          stake = Math.floor(value);
        }
        continue;
      }
      remaining.push(token);
    }
    return { stake, tokens: remaining };
  };

  const parseRouletteBetTokens = (tokens, defaultStake) => {
    let betType = null;
    let betValue = null;
    const remaining = [];

    for (let i = 0; i < tokens.length; i += 1) {
      const token = tokens[i];
      const lower = token.toLowerCase();

      if (lower === 'number' || lower === 'num' || lower === 'число') {
        const next = tokens[i + 1];
        const value = next !== undefined ? Number(next) : NaN;
        if (Number.isInteger(value) && value >= 0 && value <= 36) {
          betType = 'number';
          betValue = value;
          i += 1;
          continue;
        }
        return { error: 'Укажите число от 0 до 36 после ключевого слова number.' };
      }

      if (/^#?\d+$/.test(lower)) {
        const value = Number(lower.replace('#', ''));
        if (Number.isInteger(value) && value >= 0 && value <= 36) {
          betType = 'number';
          betValue = value;
          continue;
        }
        return { error: 'Число для ставки должно быть от 0 до 36.' };
      }

      if (lower === 'color' || lower === 'colour' || lower === 'цвет') {
        const next = tokens[i + 1];
        const value = next ? colorAliases[next.toLowerCase()] : null;
        if (!value) {
          return { error: 'Укажите цвет (red/black/green) после слова color.' };
        }
        betType = 'color';
        betValue = value;
        i += 1;
        continue;
      }

      if (colorAliases[lower]) {
        betType = 'color';
        betValue = colorAliases[lower];
        continue;
      }

      if (lower === 'parity' || lower === 'четность' || lower === 'чётность') {
        const next = tokens[i + 1];
        const value = next ? parityAliases[next.toLowerCase()] : null;
        if (!value) {
          return { error: 'Укажите odd или even после слова parity.' };
        }
        betType = 'parity';
        betValue = value;
        i += 1;
        continue;
      }

      if (parityAliases[lower]) {
        betType = 'parity';
        betValue = parityAliases[lower];
        continue;
      }

      if (lower.startsWith('bet=')) {
        const betValueRaw = lower.split('=')[1];
        if (colorAliases[betValueRaw]) {
          betType = 'color';
          betValue = colorAliases[betValueRaw];
          continue;
        }
        if (parityAliases[betValueRaw]) {
          betType = 'parity';
          betValue = parityAliases[betValueRaw];
          continue;
        }
        const numValue = Number(betValueRaw);
        if (Number.isInteger(numValue) && numValue >= 0 && numValue <= 36) {
          betType = 'number';
          betValue = numValue;
          continue;
        }
        return { error: 'Некорректное значение после bet=.' };
      }

      remaining.push(token);
    }

    if (!betType) {
      betType = 'parity';
      betValue = 'even';
    }

    return { bet: { type: betType, value: betValue, stake: defaultStake }, tokens: remaining };
  };

  const renderCasinoAgePrompt = () => buildAsciiTable(
    ['КАЗИНО 18+'],
    [
      ['Введите ваш возраст (числом).'],
      ['Доступно только с 18 лет.'],
      ['Нажмите q для выхода.'],
    ],
  );

  const renderCasinoDashboard = (age, balance, stake) => {
    const rows = [
      ['Возраст', age ? String(age) : '—'],
      ['Баланс', String(balance)],
      ['Ставка', String(stake)],
      ['1 — слоты', 'Запуск слот-машины'],
      ['2 — рулетка', 'Классическая рулетка'],
      ['q — выход', 'Возврат в терминал'],
    ];
    return buildAsciiTable(['Параметр', 'Значение'], rows);
  };

  const showCasinoAgePrompt = (pendingMode = null) => {
    if (TerminalApp.revokeCasinoAge) TerminalApp.revokeCasinoAge();
    if (!pendingMode && TerminalApp.clearCasinoPendingMode) TerminalApp.clearCasinoPendingMode();
    if (TerminalApp.setCasinoAwaitingMode) TerminalApp.setCasinoAwaitingMode(false);
    if (TerminalApp.setCasinoAwaitingSpin) TerminalApp.setCasinoAwaitingSpin(false);
    if (TerminalApp.setCasinoAwaitingReplay) TerminalApp.setCasinoAwaitingReplay(false);
    if (TerminalApp.setCasinoAwaitingAge) TerminalApp.setCasinoAwaitingAge(true, pendingMode || undefined);
    TerminalApp.printHtml(`<pre class="ascii">${renderCasinoAgePrompt()}</pre>`);
    TerminalApp.print('Введите ваш возраст (числом) или нажмите q для выхода.');
  };

  const showCasinoDashboard = () => {
    if (TerminalApp.setCasinoAwaitingAge) TerminalApp.setCasinoAwaitingAge(false);
    if (TerminalApp.setCasinoAwaitingReplay) TerminalApp.setCasinoAwaitingReplay(false);
    if (TerminalApp.setCasinoAwaitingSpin) TerminalApp.setCasinoAwaitingSpin(false);
    if (TerminalApp.clearCasinoPendingMode) TerminalApp.clearCasinoPendingMode();
    const casinoState = TerminalApp.getCasinoState
      ? TerminalApp.getCasinoState()
      : { balance: 0, stake: CASINO_CONFIG.spinCost };
    const stake = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : CASINO_CONFIG.spinCost;
    const age = TerminalApp.getCasinoAgeValue ? TerminalApp.getCasinoAgeValue() : null;
    if (TerminalApp.setCasinoAwaitingMode) TerminalApp.setCasinoAwaitingMode(true);
    TerminalApp.printHtml(`<pre class="ascii">${renderCasinoDashboard(age, casinoState.balance, stake)}</pre>`);
    TerminalApp.print('Выберите игру цифрой: 1 — слоты, 2 — рулетка. Нажмите q для выхода.');
  };

  const queueCasinoRound = (mode, options = {}) => {
    const normalizedMode = mode === 'slots' ? 'slots' : 'roulette';
    const defaultStake = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : CASINO_CONFIG.spinCost;
    const requestedStake = Number.isFinite(options.stake) && options.stake > 0 ? Math.floor(options.stake) : defaultStake;
    const providedBet = options.bet;

    if (TerminalApp.setCasinoAwaitingMode) TerminalApp.setCasinoAwaitingMode(false);
    if (TerminalApp.setCasinoLastMode) TerminalApp.setCasinoLastMode(normalizedMode);
    if (TerminalApp.setCasinoPendingMode) TerminalApp.setCasinoPendingMode(normalizedMode);
    if (TerminalApp.setCasinoStake) TerminalApp.setCasinoStake(requestedStake);
    if (TerminalApp.setCasinoAwaitingReplay) TerminalApp.setCasinoAwaitingReplay(false);
    if (TerminalApp.setCasinoAwaitingSpin) TerminalApp.setCasinoAwaitingSpin(false);

    let activeBet = null;
    if (normalizedMode === 'roulette') {
      activeBet = providedBet && providedBet.type ? { ...providedBet } : (TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : null);
      if (!activeBet || !activeBet.type) {
        activeBet = { type: 'parity', value: 'even', stake: requestedStake };
      }
      if (!Number.isFinite(activeBet.stake) || activeBet.stake <= 0) {
        activeBet.stake = requestedStake;
      }
      if (TerminalApp.setCasinoBet) TerminalApp.setCasinoBet(activeBet);
    } else if (TerminalApp.clearCasinoBet) {
      TerminalApp.clearCasinoBet();
    }

    const ageConfirmed = TerminalApp.isCasinoAgeConfirmed ? TerminalApp.isCasinoAgeConfirmed() : false;
    if (!ageConfirmed) {
      showCasinoAgePrompt(normalizedMode);
      return;
    }

    const betForPrompt = normalizedMode === 'roulette'
      ? (TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : activeBet)
      : null;
    const stakeForPrompt = normalizedMode === 'roulette'
      ? (betForPrompt && Number.isFinite(betForPrompt.stake) && betForPrompt.stake > 0 ? betForPrompt.stake : requestedStake)
      : requestedStake;

    if (normalizedMode === 'slots') {
      const stateForPreview = TerminalApp.getCasinoState
        ? TerminalApp.getCasinoState()
        : { balance: CASINO_CONFIG.spinCost * 10 };
      const preview = renderSlotMachine([0, 0, 0], stateForPreview.balance, requestedStake, 'Готовы к вращению? (q — выход)');
      TerminalApp.printHtml(`<pre class="ascii">${preview}</pre>`);
    }

    if (TerminalApp.setCasinoAwaitingSpin) TerminalApp.setCasinoAwaitingSpin(true, normalizedMode);
    TerminalApp.print(buildSpinPrompt(normalizedMode, stakeForPrompt, betForPrompt));
  };

  const deductCasinoStake = (stake) => {
    const state = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : { balance: 0, initialBalance: 0 };
    if (state.balance < stake) {
      return { ok: false, balance: state.balance };
    }
    if (TerminalApp.adjustCasinoBalance) {
      TerminalApp.adjustCasinoBalance(-stake);
    }
    const after = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : state;
    return { ok: true, balance: after.balance };
  };

  const playSlotRound = async (stake) => {
    const { output } = TerminalApp.elements;
    if (!output) {
      TerminalApp.print('Error: terminal unavailable', 'error');
      return { played: false };
    }

    const deduct = deductCasinoStake(stake);
    if (!deduct.ok) {
      TerminalApp.print(`Недостаточно средств для ставки ${stake}. Текущий баланс: ${deduct.balance}.`);
      return { played: false };
    }

    let spinner = TerminalApp.__slotLine;
    if (!spinner || !spinner.isConnected) {
      spinner = document.createElement('div');
      spinner.className = 'slot-machine-line';
      TerminalApp.__slotLine = spinner;
      output.appendChild(spinner);
    } else {
      output.appendChild(spinner);
    }

    let digits = createSlotDigits();
    for (let i = 0; i < CASINO_CONFIG.frames; i += 1) {
      digits = createSlotDigits();
      const currentState = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : { balance: 0 };
      spinner.innerHTML = `<pre>${renderSlotMachine(digits, currentState.balance, stake)}</pre>`;
      output.scrollTop = output.scrollHeight;
      // eslint-disable-next-line no-await-in-loop
      await sleep(CASINO_CONFIG.frameDelay + i * CASINO_CONFIG.frameDelayStep);
    }

    const [a, b, c] = digits;
    let payout = 0;
    let message = 'Ничего не выпало. Попробуйте ещё раз.';
    if (a === b && b === c) {
      payout = CASINO_CONFIG.jackpotPayout;
      message = `JACKPOT! Все цифры ${a}. Выигрыш ${payout}.`;
    } else if (a === b || b === c || a === c) {
      payout = CASINO_CONFIG.pairPayout;
      message = `Есть совпадение! Выигрыш ${payout}.`;
    } else {
      message = `Не повезло. Потеря ${stake}.`;
    }

    if (payout > 0 && TerminalApp.adjustCasinoBalance) {
      TerminalApp.adjustCasinoBalance(payout);
    }

    const finalState = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : { balance: 0 };
    spinner.innerHTML = `<pre>${renderSlotMachine(digits, finalState.balance, stake, message)}</pre>`;
    output.scrollTop = output.scrollHeight;

    if (payout > 0) {
      TerminalApp.print(`Баланс: ${finalState.balance} (выигрыш ${payout})`);
    } else {
      TerminalApp.print(`Баланс: ${finalState.balance} (ставка ${stake})`);
    }

    if (finalState.balance <= 0) {
      TerminalApp.print(`Баланс обнулён. Введите "casino reset", чтобы восстановить ${finalState.initialBalance ?? stake * 10}.`);
    }

    return { played: true };
  };

  const playRouletteRound = async (stake, bet) => {
    const { output } = TerminalApp.elements;
    if (!output) {
      TerminalApp.print('Error: terminal unavailable', 'error');
      return { played: false };
    }

    const activeBet = bet && bet.type ? { ...bet } : { type: 'parity', value: 'even', stake };
    const stakeToUse = Number.isFinite(activeBet.stake) && activeBet.stake > 0 ? Math.floor(activeBet.stake) : stake;

    const deduct = deductCasinoStake(stakeToUse);
    if (!deduct.ok) {
      TerminalApp.print(`Недостаточно средств для ставки ${stakeToUse}. Текущий баланс: ${deduct.balance}.`);
      return { played: false };
    }

    let wheel = TerminalApp.__rouletteLine;
    if (!wheel || !wheel.isConnected) {
      wheel = document.createElement('div');
      wheel.className = 'roulette-line';
      TerminalApp.__rouletteLine = wheel;
      output.appendChild(wheel);
    } else {
      output.appendChild(wheel);
    }

    let number = Math.floor(Math.random() * 37);
    const frames = CASINO_CONFIG.frames + 4;
    for (let i = 0; i < frames; i += 1) {
      number = Math.floor(Math.random() * 37);
      const currentState = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : { balance: 0 };
      wheel.innerHTML = `<pre>${renderRouletteFrame(number, currentState.balance, stakeToUse)}</pre>`;
      output.scrollTop = output.scrollHeight;
      // eslint-disable-next-line no-await-in-loop
      await sleep(CASINO_CONFIG.frameDelay + i * CASINO_CONFIG.frameDelayStep);
    }

    const finalNumber = Math.floor(Math.random() * 37);
    const color = rouletteColor(finalNumber);
    let payout = 0;
    let won = false;

    const finalColorKey = finalNumber === 0 ? 'green' : (finalNumber % 2 === 0 ? 'red' : 'black');

    if (activeBet.type === 'number') {
      if (Number(activeBet.value) === finalNumber) {
        payout = stakeToUse * 36;
        won = true;
      }
    } else if (activeBet.type === 'color') {
      if (activeBet.value === 'green') {
        if (finalNumber === 0) {
          payout = stakeToUse * 36;
          won = true;
        }
      } else if (finalNumber !== 0 && activeBet.value === finalColorKey) {
        payout = stakeToUse * 2;
        won = true;
      }
    } else {
      if (finalNumber !== 0) {
        const isEven = finalNumber % 2 === 0;
        if ((activeBet.value === 'even' && isEven) || (activeBet.value === 'odd' && !isEven)) {
          payout = stakeToUse * 2;
          won = true;
        }
      }
    }

    if (payout > 0 && TerminalApp.adjustCasinoBalance) {
      TerminalApp.adjustCasinoBalance(payout);
    }

    let message;
    const betDescription = describeRouletteBet(activeBet);
    if (won) {
      const profit = payout - stakeToUse;
      message = `Ставка: ${betDescription}. Выпало ${finalNumber} (${color.label}). Выигрыш ${payout} (прибыль ${profit}).`;
    } else {
      message = `Ставка: ${betDescription}. Выпало ${finalNumber} (${color.label}). Потеря ${stakeToUse}.`;
    }

    const finalState = TerminalApp.getCasinoState ? TerminalApp.getCasinoState() : { balance: 0 };
    wheel.innerHTML = `<pre>${renderRouletteFrame(finalNumber, finalState.balance, stakeToUse, message)}</pre>`;
    output.scrollTop = output.scrollHeight;

    if (payout > 0) {
      TerminalApp.print(`Баланс: ${finalState.balance} (выигрыш ${payout})`);
    } else {
      TerminalApp.print(`Баланс: ${finalState.balance} (ставка ${stakeToUse})`);
    }

    if (finalState.balance <= 0) {
      TerminalApp.print(`Баланс обнулён. Введите "casino reset", чтобы восстановить ${finalState.initialBalance ?? stakeToUse * 10}.`);
    }

    return { played: true };
  };

  const playCasinoGame = async (mode, options = {}) => {
    const normalizedMode = mode === 'slots' ? 'slots' : 'roulette';
    const defaultStake = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : CASINO_CONFIG.spinCost;
    let stake = Number.isFinite(options.stake) && options.stake > 0 ? Math.floor(options.stake) : defaultStake;
    let bet = options.bet;
    let result = { played: false };

    if (normalizedMode === 'slots') {
      TerminalApp.clearCasinoBet && TerminalApp.clearCasinoBet();
      result = await playSlotRound(stake);
    } else {
      if (!bet || !bet.type) {
        bet = TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : null;
      }
      if (!bet || !bet.type) {
        bet = { type: 'parity', value: 'even', stake };
      }
      if (!Number.isFinite(bet.stake) || bet.stake <= 0) {
        bet.stake = stake;
      }
      stake = bet.stake;
      TerminalApp.setCasinoBet && TerminalApp.setCasinoBet(bet);
      result = await playRouletteRound(stake, bet);
    }

    if (result.played) {
      TerminalApp.setCasinoLastMode && TerminalApp.setCasinoLastMode(normalizedMode);
      TerminalApp.setCasinoPendingMode && TerminalApp.setCasinoPendingMode(normalizedMode);
      TerminalApp.setCasinoStake && TerminalApp.setCasinoStake(stake);
      TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(true, normalizedMode);
      TerminalApp.print('Сыграть ещё? (y/n, q — выход)');
    } else {
      TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
    }
    return result.played;
  };

  const normalizeCellValue = (value) => {
    if (value === null || value === undefined) return '';
    return String(value).replace(/\s+/g, ' ').trim();
  };

  const buildAsciiTable = (headers, rows) => {
    if (!headers || !headers.length) return '';
    const processedRows = rows.map((row) => headers.map((_, idx) => normalizeCellValue(row[idx])));
    const widths = headers.map((header, idx) => {
      const cellLengths = processedRows.map((row) => row[idx]?.length || 0);
      return Math.max(header.length, 3, ...cellLengths);
    });

    const border = `+${widths.map((w) => '-'.repeat(w + 2)).join('+')}+`;
    const formatLine = (cells) => `|${cells.map((cell, idx) => ` ${cell.padEnd(widths[idx], ' ')} `).join('|')}|`;
    const headerLine = formatLine(headers);

    const lines = [border, headerLine, border];
    if (processedRows.length === 0) {
      const emptyCells = headers.map(() => '—');
      lines.push(formatLine(emptyCells));
    } else {
      processedRows.forEach((row) => {
        lines.push(formatLine(row));
      });
    }
    lines.push(border);
    return lines.join('\n');
  };

  const escapeHtml = (text) => text.replace(/[&<>"']/g, (ch) => {
    switch (ch) {
      case '&':
        return '&amp;';
      case '<':
        return '&lt;';
      case '>':
        return '&gt;';
      case '"':
        return '&quot;';
      case "'":
        return '&#39;';
      default:
        return ch;
    }
  });

  const getCommonPrefix = (items) => {
    if (!items.length) return '';
    return items.reduce((prefix, item) => {
      let i = 0;
      const limit = Math.min(prefix.length, item.length);
      while (i < limit && prefix[i] === item[i]) i += 1;
      return prefix.slice(0, i);
    });
  };

  const computeAutocompleteSuggestion = () => {
    const { input } = TerminalApp.elements;
    if (!input) return null;

    const value = input.value;
    const caretIndex = input.selectionStart ?? value.length;
    if (caretIndex !== value.length) return null;

    const beforeCaret = value.slice(0, caretIndex);
    if (!beforeCaret || beforeCaret.trim().length === 0) return null;
    if (beforeCaret.includes(' ')) return null;

    const partial = beforeCaret.trim();
    const partialLower = partial.toLowerCase();
    if (!partialLower) return null;

    const matches = commandsList.filter((cmd) => cmd.startsWith(partialLower));
    if (!matches.length) return null;

    const unique = matches.length === 1;
    let target = null;

    if (unique) {
      target = matches[0];
      if (commandsWithArgs.has(target) && !value.endsWith(' ')) {
        target += ' ';
      }
    } else {
      const prefix = getCommonPrefix(matches);
      if (prefix.length > partialLower.length) {
        target = prefix;
      }
    }

    if (!target) {
      return { beforeCaret, matches, unique, completion: '', target: null };
    }

    const completion = target.slice(partialLower.length);
    if (!completion) {
      return { beforeCaret, matches, unique, completion: '', target: null };
    }

    return { beforeCaret, matches, unique, completion, target };
  };

  TerminalApp.refreshAutocompleteHint = () => {
    const { hint, input } = TerminalApp.elements;
    if (!hint) return;

    const suggestion = computeAutocompleteSuggestion();
    if (!suggestion || !suggestion.completion || !suggestion.completion.trim()) {
      hint.textContent = '';
      if (hint.style) hint.style.transform = 'translateY(-50%)';
      return;
    }

    const scrollLeft = input ? input.scrollLeft : 0;
    hint.style.transform = `translate(${-scrollLeft}px, -50%)`;
    hint.innerHTML = `<span class="ghost-hidden">${escapeHtml(suggestion.beforeCaret)}</span>${escapeHtml(suggestion.completion)}`;
  };

  TerminalApp.CURRENCY_LIST = [
    ['EUR', 'Euro'],
    ['USD', 'US Dollar'],
    ['JPY', 'Japanese Yen'],
    ['BGN', 'Bulgarian Lev'],
    ['CZK', 'Czech Republic Koruna'],
    ['DKK', 'Danish Krone'],
    ['GBP', 'British Pound Sterling'],
    ['HUF', 'Hungarian Forint'],
    ['PLN', 'Polish Zloty'],
    ['RON', 'Romanian Leu'],
    ['SEK', 'Swedish Krona'],
    ['CHF', 'Swiss Franc'],
    ['ISK', 'Icelandic Króna'],
    ['NOK', 'Norwegian Krone'],
    ['HRK', 'Croatian Kuna'],
    ['RUB', 'Russian Ruble'],
    ['TRY', 'Turkish Lira'],
    ['AUD', 'Australian Dollar'],
    ['BRL', 'Brazilian Real'],
    ['CAD', 'Canadian Dollar'],
    ['CNY', 'Chinese Yuan'],
    ['HKD', 'Hong Kong Dollar'],
    ['IDR', 'Indonesian Rupiah'],
    ['ILS', 'Israeli New Sheqel'],
    ['INR', 'Indian Rupee'],
    ['KRW', 'South Korean Won'],
    ['MXN', 'Mexican Peso'],
    ['MYR', 'Malaysian Ringgit'],
    ['NZD', 'New Zealand Dollar'],
    ['PHP', 'Philippine Peso'],
    ['SGD', 'Singapore Dollar'],
    ['THB', 'Thai Baht'],
    ['ZAR', 'South African Rand'],
  ];
  TerminalApp.CURRENCY_MAP = Object.fromEntries(TerminalApp.CURRENCY_LIST);

  TerminalApp.showHelp = () => {
    TerminalApp.print('Добро пожаловать в терминал погоды и рейсов');
    TerminalApp.printHtml('<span class="big">Терминальный дашборд</span>');
    TerminalApp.print('Доступные команды:');
    helpItems.forEach((entry) => TerminalApp.print(`- ${entry}`));
    TerminalApp.print('Подсказка: команда timezone принимает значения вроде +3 или -5.5');
  };

  TerminalApp.autocompleteCommand = () => {
    const { input } = TerminalApp.elements;
    if (!input) return;

    const suggestion = computeAutocompleteSuggestion();
    if (!suggestion) return;

    const { target, matches, unique } = suggestion;
    if (target) {
      const caretIndex = input.selectionStart ?? input.value.length;
      const rest = input.value.slice(caretIndex);
      input.value = target + rest;
      const pos = target.length;
      input.setSelectionRange(pos, pos);
      requestAnimationFrame(() => {
        TerminalApp.updateCursorPosition();
        TerminalApp.refreshAutocompleteHint();
      });
      if (!unique && matches && matches.length > 1) {
        TerminalApp.print(`Suggestions: ${matches.join('  ')}`);
      }
      return;
    }

    if (matches && matches.length > 1) {
      TerminalApp.print(`Suggestions: ${matches.join('  ')}`);
    }
    TerminalApp.refreshAutocompleteHint();
  };

  TerminalApp.executeCommand = async (raw) => {
    const parts = raw.split(/\s+/).filter(Boolean);
    if (parts.length === 0) return;
    const cmd = parts[0].toLowerCase();
    const arg = parts.slice(1).join(' ');
    const trimmedInput = raw.trim();
    const lowerTrimmed = trimmedInput.toLowerCase();
    const isCasinoCommand = cmd === 'casino';
    const isKnownCommand = commandsList.includes(cmd);

    const awaitingAge = TerminalApp.isCasinoAwaitingAge && TerminalApp.isCasinoAwaitingAge();
    if (awaitingAge) {
      if (lowerTrimmed === 'q') {
        TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(false);
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
        TerminalApp.revokeCasinoAge && TerminalApp.revokeCasinoAge();
        TerminalApp.print('Вы вышли из казино.');
        return;
      }

      if (lowerTrimmed === 'casino') {
        showCasinoAgePrompt();
        return;
      }

      const ageValue = Number(trimmedInput.replace(',', '.'));
      const isNumericAge = trimmedInput !== '' && Number.isFinite(ageValue);

      if (isNumericAge) {
        const ageInt = Math.floor(ageValue);
        if (ageInt <= 18) {
          TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(false);
          TerminalApp.revokeCasinoAge && TerminalApp.revokeCasinoAge();
          TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
          TerminalApp.print('Казино доступно только пользователям старше 18 лет.');
          return;
        }

        TerminalApp.confirmCasinoAge && TerminalApp.confirmCasinoAge(ageInt);
        TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(false);
        TerminalApp.print(`Возраст подтверждён: ${ageInt}.`);
        showCasinoDashboard();
        return;
      }

      if (!isCasinoCommand && isKnownCommand) {
        TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(false);
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
      } else {
        TerminalApp.print('Пожалуйста, введите возраст числом.');
        return;
      }
    }

    const awaitingMode = TerminalApp.isCasinoAwaitingMode && TerminalApp.isCasinoAwaitingMode();
    if (awaitingMode) {
      if (lowerTrimmed === 'q') {
        TerminalApp.setCasinoAwaitingMode && TerminalApp.setCasinoAwaitingMode(false);
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
        TerminalApp.print('Вы вышли из казино.');
        return;
      }

      if (lowerTrimmed === 'casino') {
        showCasinoDashboard();
        return;
      }

      if (trimmedInput) {
        const primaryChoice = trimmedInput.split(/\s+/)[0].toLowerCase();
        let selectedMode = null;
        if (['1', 'slots', 'slot', 'слоты', 'слот', 'machine'].includes(primaryChoice)) {
          selectedMode = 'slots';
        } else if (['2', 'roulette', 'рулетка'].includes(primaryChoice)) {
          selectedMode = 'roulette';
        }

        if (selectedMode) {
          TerminalApp.print(selectedMode === 'slots' ? 'Вы выбрали слот-машину.' : 'Вы выбрали рулетку.');
          queueCasinoRound(selectedMode);
          return;
        }
      }

      if (!isCasinoCommand && isKnownCommand) {
        TerminalApp.setCasinoAwaitingMode && TerminalApp.setCasinoAwaitingMode(false);
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
      } else {
        TerminalApp.print('Выберите 1 для слотов или 2 для рулетки.');
        showCasinoDashboard();
        return;
      }
    }

    const awaitingSpin = TerminalApp.isCasinoAwaitingSpin && TerminalApp.isCasinoAwaitingSpin();
    const awaitingReplay = TerminalApp.isCasinoAwaitingReplay && TerminalApp.isCasinoAwaitingReplay();

    if (awaitingSpin || awaitingReplay) {
      if (lowerTrimmed === 'casino') {
        showCasinoAgePrompt();
        return;
      }

      if (lowerTrimmed === 'q') {
        if (awaitingSpin) {
          TerminalApp.setCasinoAwaitingSpin && TerminalApp.setCasinoAwaitingSpin(false);
        }
        if (awaitingReplay) {
          TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
        }
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
        TerminalApp.print('Вы вышли из казино.');
        return;
      }

      if (isYesResponse(raw) || isNoResponse(raw)) {
        const pendingMode = (TerminalApp.getCasinoPendingMode && TerminalApp.getCasinoPendingMode())
          || (TerminalApp.getCasinoLastMode && TerminalApp.getCasinoLastMode())
          || 'roulette';
        const defaultStake = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : CASINO_CONFIG.spinCost;
        const betFromState = TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : null;
        const betStake = betFromState && Number.isFinite(betFromState.stake) && betFromState.stake > 0
          ? betFromState.stake
          : defaultStake;

        if (isYesResponse(raw)) {
          if (awaitingSpin) {
            TerminalApp.setCasinoAwaitingSpin && TerminalApp.setCasinoAwaitingSpin(false);
            TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
            const played = await playCasinoGame(pendingMode, { stake: betStake, bet: betFromState });
            if (!played && TerminalApp.clearCasinoPendingMode) {
              TerminalApp.clearCasinoPendingMode();
            }
            if (!played) {
              showCasinoDashboard();
            }
            return;
          }

          TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
          const replayBet = TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : betFromState;
          const replayStake = replayBet && Number.isFinite(replayBet.stake) && replayBet.stake > 0
            ? replayBet.stake
            : defaultStake;
          const played = await playCasinoGame(pendingMode, { stake: replayStake, bet: replayBet });
          if (!played && TerminalApp.clearCasinoPendingMode) {
            TerminalApp.clearCasinoPendingMode();
          }
          if (!played) {
            showCasinoDashboard();
          }
          return;
        }

        if (awaitingSpin) {
          TerminalApp.setCasinoAwaitingSpin && TerminalApp.setCasinoAwaitingSpin(false);
          TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
          TerminalApp.print('Ставка отменена.');
          showCasinoDashboard();
          return;
        }
        TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
        TerminalApp.print('Игра завершена. Возвращайтесь позже.');
        showCasinoDashboard();
        return;
      }

      if (!isCasinoCommand && isKnownCommand) {
        if (awaitingSpin) {
          TerminalApp.setCasinoAwaitingSpin && TerminalApp.setCasinoAwaitingSpin(false);
        }
        if (awaitingReplay) {
          TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
        }
        TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
      } else {
        TerminalApp.print('Ответьте y или n.');
        return;
      }
    }

    if (cmd === 'help') {
      TerminalApp.showHelp();
      return;
    }

    if (cmd === 'admin') {
      TerminalApp.print('Загрузка админ-панели...');
      try {
        const resp = await fetch('/api/admin/overview/', { credentials: 'same-origin' });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          const message = (data && data.error) || resp.statusText || 'Неизвестная ошибка';
          TerminalApp.print(`Error: ${message}`, 'error');
          return;
        }

        const formatTime = (timestamp) => {
          if (!timestamp) return '-';
          const formatted = TerminalApp.formatHistoryTime(timestamp);
          return formatted || timestamp;
        };

        const totals = data.totals || {};
        const metricLabels = {
          users_total: 'Пользователи',
          tasks_total: 'Задачи',
          searches_total: 'Поиски',
        };
        const totalsRows = Object.entries(totals).map(([key, value]) => [metricLabels[key] || key, String(value)]);
        if (totalsRows.length) {
          TerminalApp.printHtml(`<pre>${buildAsciiTable(['Метрика', 'Значение'], totalsRows)}</pre>`);
        }

        const usersRows = (data.users || []).map((user) => [
          normalizeCellValue(user.username || '-'),
          user.is_staff ? 'staff' : '-',
          formatTime(user.date_joined),
          formatTime(user.last_login),
          String(user.tasks_count ?? 0),
          String(user.searches_count ?? 0),
        ]);
        if (usersRows.length) {
          TerminalApp.printHtml(`<pre>${buildAsciiTable(['Пользователь', 'Роль', 'Создан', 'Последний вход', 'Задачи', 'Поиски'], usersRows)}</pre>`);
        } else {
          TerminalApp.print('Пользователи не найдены.');
        }

        const shorten = (value, limit = 32) => {
          const base = normalizeCellValue(value);
          return base.length > limit ? `${base.slice(0, limit - 3)}...` : base;
        };

        const tasksRows = (data.recent_tasks || []).map((task) => [
          String(task.id),
          normalizeCellValue(task.user || '-'),
          normalizeCellValue(task.city || '-'),
          shorten(task.text || ''),
          formatTime(task.created_at),
        ]);
        if (tasksRows.length) {
          TerminalApp.printHtml(`<pre>${buildAsciiTable(['ID', 'Пользователь', 'Город', 'Текст', 'Создано'], tasksRows)}</pre>`);
        } else {
          TerminalApp.print('Нет сохранённых задач.');
        }

        const searchesRows = (data.recent_searches || []).map((item) => [
          normalizeCellValue(item.user || '-'),
          normalizeCellValue(item.city || '-'),
          formatTime(item.created_at),
        ]);
        if (searchesRows.length) {
          TerminalApp.printHtml(`<pre>${buildAsciiTable(['Пользователь', 'Город', 'Когда'], searchesRows)}</pre>`);
        } else {
          TerminalApp.print('История поисков пуста.');
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'casino') {
      if (TerminalApp.setCasinoAwaitingMode) TerminalApp.setCasinoAwaitingMode(false);

      let tokens = parts.slice(1);
      const lowerTokens = tokens.map((token) => String(token).toLowerCase());
      const casinoState = TerminalApp.getCasinoState
        ? TerminalApp.getCasinoState()
        : { balance: 0, initialBalance: CASINO_CONFIG.spinCost * 10, ageConfirmed: false, stake: CASINO_CONFIG.spinCost };
      const defaultStake = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : CASINO_CONFIG.spinCost;

      if (tokens.length === 0) {
        showCasinoAgePrompt();
        return;
      }

      const primary = lowerTokens[0];
      if (primary === 'help') {
        TerminalApp.print('Команды казино:');
        TerminalApp.print('- casino — открыть меню выбора игры');
        TerminalApp.print('- casino slots [stake N] — слот-машина');
        TerminalApp.print('- casino roulette [number X|red|black|green|odd|even] [stake N] — рулетка');
        TerminalApp.print('- casino stake <N> — изменить ставку по умолчанию');
        TerminalApp.print('- casino status — баланс и параметры');
        TerminalApp.print(`- casino reset — восстановить баланс до ${casinoState.initialBalance || 100}`);
        TerminalApp.print('Перед запуском и перед повтором отвечайте y/n.');
        TerminalApp.print('Нажмите q в любом меню казино, чтобы выйти обратно в терминал.');
        return;
      }

      if (primary === 'status' || primary === 'balance') {
        const bet = TerminalApp.getCasinoBet ? TerminalApp.getCasinoBet() : null;
        const lastMode = TerminalApp.getCasinoLastMode ? TerminalApp.getCasinoLastMode() : 'roulette';
        const stakeValue = TerminalApp.getCasinoStake ? TerminalApp.getCasinoStake() : (casinoState.stake ?? defaultStake);
        TerminalApp.print(`Баланс: ${casinoState.balance}; начальный: ${casinoState.initialBalance}; ставка: ${stakeValue}; возраст подтверждён: ${casinoState.ageConfirmed ? 'да' : 'нет'}; последняя игра: ${lastMode}`);
        if (bet && bet.type) {
          TerminalApp.print(`Текущая ставка рулетки: ${describeRouletteBet(bet)} (ставка ${bet.stake ?? defaultStake})`);
        }
        return;
      }

      if (primary === 'reset') {
        const updated = TerminalApp.resetCasinoBalance ? TerminalApp.resetCasinoBalance() : casinoState.initialBalance;
        TerminalApp.clearCasinoBet && TerminalApp.clearCasinoBet();
        TerminalApp.print(`Баланс восстановлен до ${updated}.`);
        return;
      }

      if (primary === 'stake' || primary.startsWith('stake=')) {
        const parsedStake = parseStakeTokens(tokens, defaultStake).stake;
        TerminalApp.setCasinoStake && TerminalApp.setCasinoStake(parsedStake);
        TerminalApp.print(`Ставка по умолчанию установлена: ${parsedStake}.`);
        return;
      }

      let mode = null;
      const filteredTokens = [];
      tokens.forEach((token) => {
        const lower = token.toLowerCase();
        if (!mode && ['1', 'slots', 'slot', 'слоты', 'слот', 'machine'].includes(lower)) {
          mode = 'slots';
          return;
        }
        if (!mode && ['2', 'roulette', 'рулетка'].includes(lower)) {
          mode = 'roulette';
          return;
        }
        filteredTokens.push(token);
      });
      tokens = filteredTokens;
      if (!mode) {
        mode = (TerminalApp.getCasinoLastMode && TerminalApp.getCasinoLastMode()) || 'roulette';
      }

      const stakeInfo = parseStakeTokens(tokens, defaultStake);
      let stake = stakeInfo.stake;
      tokens = stakeInfo.tokens;

      let bet = null;
      if (mode === 'roulette') {
        const betInfo = parseRouletteBetTokens(tokens, stake);
        if (betInfo.error) {
          TerminalApp.print(betInfo.error, 'error');
          return;
        }
        bet = betInfo.bet;
        bet.stake = stake;
      }
      queueCasinoRound(mode, { stake, bet });
      return;
    }

    if (cmd === 'fetch') {
      TerminalApp.printHtml(`<pre class="ascii">${TerminalApp.asciiIcons.arch}</pre>`);
      const info = [
        'User: guest',
        'Host: nebula-hub',
        'OS: Arch Linux x86_64 (mock)',
        'Kernel: 6.8.0-arch1-1',
        'Uptime: 3h 21m',
        'Shell: web-terminal 1.0',
        'Packages: 420 (pacman)',
        'Resolution: 1920x1080',
        'WM: Tiling (mock)',
        'CPU: Virtual Quad-Core @ 3.20GHz',
        'GPU: Integrated WebGL',
        'Memory: 4096MiB / 8192MiB',
      ];
      info.forEach((line) => TerminalApp.print(line));
      return;
    }

    if (cmd === 'clear') {
      if (TerminalApp.elements.output) TerminalApp.elements.output.innerHTML = '';
      TerminalApp.print('Подсказка: введите "help" для списка команд.');
      return;
    }

    if (cmd === 'signup') {
      const [username, password] = (arg || '').split(/\s+/);
      if (!username || !password) {
        TerminalApp.print('Error: используйте signup <логин> <пароль>', 'error');
        return;
      }
      TerminalApp.print(`Создание аккаунта ${username}...`);
      try {
        const resp = await fetch('/api/auth/register/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ username, password }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser(data.username || username);
        TerminalApp.updatePrompt();
        TerminalApp.print(data.message || 'Регистрация завершена');
        await TerminalApp.fetchHistory();
        try {
          await TerminalApp.fetchTasks();
        } catch (err) {
          // ignore fetch errors here
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'login') {
      const [username, password] = (arg || '').split(/\s+/);
      if (!username || !password) {
        TerminalApp.print('Error: используйте login <логин> <пароль>', 'error');
        return;
      }
      TerminalApp.print(`Авторизация ${username}...`);
      try {
        const resp = await fetch('/api/auth/login/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ username, password }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser(data.username || username);
        TerminalApp.updatePrompt();
        TerminalApp.print(data.message || 'Авторизация успешна');
        await TerminalApp.fetchHistory();
        try {
          await TerminalApp.fetchTasks();
        } catch (err) {
          // ignore fetch errors here
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'timezone') {
      if (!arg) {
        TerminalApp.print('Error: provide offset, e.g. timezone +3 or timezone -5.5', 'error');
        return;
      }
      const val = parseFloat(arg);
      if (!Number.isFinite(val)) {
        TerminalApp.print('Error: invalid offset', 'error');
        return;
      }
      TerminalApp.setTimezoneOffset(val);
      TerminalApp.updateClockDisplay();
      const sign = val >= 0 ? '+' : '';
      TerminalApp.print(`Timezone set to UTC${sign}${val}`);
      return;
    }

    if (cmd === 'note') {
      if (!arg) {
        TerminalApp.print('Error: note text required', 'error');
        return;
      }
      TerminalApp.addNote(arg);
      const count = TerminalApp.getNotes().length;
      TerminalApp.print(`Note saved (#${count})`);
      return;
    }

    if (cmd === 'notes') {
      const notes = TerminalApp.getNotes();
      if (notes.length === 0) {
        TerminalApp.print('No notes yet.');
        return;
      }
      TerminalApp.print('Notes:');
      notes.forEach((n, i) => TerminalApp.print(`${i + 1}. ${n}`));
      return;
    }

    if (cmd === 'tasks') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      try {
        const tasks = await TerminalApp.fetchTasks();
        if (!tasks.length) {
          TerminalApp.print('Пока задач нет.');
          return;
        }
        TerminalApp.print('Ваши напоминания:');
        tasks.forEach((task) => {
          TerminalApp.print(TerminalApp.describeTask(task));
        });
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskadd') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = arg || '';
      const separatorIndex = rawArg.indexOf('|');
      if (separatorIndex === -1) {
        TerminalApp.print('Error: используйте taskadd <город>|<текст>', 'error');
        return;
      }
      const city = rawArg.slice(0, separatorIndex).trim();
      const text = rawArg.slice(separatorIndex + 1).trim();
      if (!city || !text) {
        TerminalApp.print('Error: укажите город и текст напоминания', 'error');
        return;
      }
      TerminalApp.print(`Сохранение задачи для ${city}...`);
      try {
        const resp = await fetch('/api/tasks/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ city, text }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        if (data.task) {
          TerminalApp.upsertTask(data.task);
          TerminalApp.print(`Задача #${data.task.id} сохранена.`);
          TerminalApp.print(TerminalApp.describeTask(data.task));
        } else {
          TerminalApp.print('Задача сохранена.');
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskupdate') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const rawArg = arg || '';
      const firstSep = rawArg.indexOf('|');
      if (firstSep === -1) {
        TerminalApp.print('Error: используйте taskupdate <id>|<город>|<текст>', 'error');
        return;
      }
      const secondPart = rawArg.slice(firstSep + 1);
      const secondSep = secondPart.indexOf('|');
      if (secondSep === -1) {
        TerminalApp.print('Error: используйте taskupdate <id>|<город>|<текст>', 'error');
        return;
      }
      const idPart = rawArg.slice(0, firstSep).trim();
      const city = secondPart.slice(0, secondSep).trim();
      const text = secondPart.slice(secondSep + 1).trim();
      const id = Number(idPart);
      if (!Number.isInteger(id) || id <= 0) {
        TerminalApp.print('Error: некорректный идентификатор задачи', 'error');
        return;
      }
      if (!city || !text) {
        TerminalApp.print('Error: укажите город и текст для обновления', 'error');
        return;
      }
      TerminalApp.print(`Обновление задачи #${id}...`);
      try {
        const resp = await fetch(`/api/tasks/${id}/`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'same-origin',
          body: JSON.stringify({ city, text }),
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        if (data.task) {
          TerminalApp.upsertTask(data.task);
          TerminalApp.print(`Задача #${data.task.id} обновлена.`);
          TerminalApp.print(TerminalApp.describeTask(data.task));
        } else {
          TerminalApp.print('Задача обновлена.');
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'taskdelete') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Error: требуется авторизация.', 'error');
        return;
      }
      const id = Number((arg || '').trim());
      if (!Number.isInteger(id) || id <= 0) {
        TerminalApp.print('Error: используйте taskdelete <id>', 'error');
        return;
      }
      TerminalApp.print(`Удаление задачи #${id}...`);
      try {
        const resp = await fetch(`/api/tasks/${id}/`, {
          method: 'DELETE',
          credentials: 'same-origin',
        });
        if (!resp.ok) {
          const data = await resp.json().catch(() => ({}));
          TerminalApp.print(`Error: ${(data && data.error) || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.removeTask(id);
        TerminalApp.print('Задача удалена.');
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'timer') {
      if (!arg || Number.isNaN(Number(arg))) {
        TerminalApp.print('Error: seconds required', 'error');
        return;
      }
      let sec = Math.max(0, Math.floor(Number(arg)));
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
      return;
    }

    if (cmd === 'logout') {
      if (TerminalApp.getCurrentUser() === 'guest') {
        TerminalApp.print('Вы не вошли в систему.');
        return;
      }
      const username = TerminalApp.getCurrentUser();
      TerminalApp.print(`Выход из аккаунта ${username}...`);
      try {
        const resp = await fetch('/api/auth/logout/', {
          method: 'POST',
          credentials: 'same-origin',
        });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.setCurrentUser('guest');
        TerminalApp.updatePrompt();
        TerminalApp.setTasks([]);
        TerminalApp.print(data.message || 'Вы вышли из системы.');
        await TerminalApp.fetchHistory();
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'weather') {
      if (!arg) {
        TerminalApp.print('Error: city required', 'error');
        return;
      }
      TerminalApp.print(`Fetching weather for ${arg}...`);
      try {
        const resp = await fetch(`/api/weather/?city=${encodeURIComponent(arg)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        const description = (data.description || '').toLowerCase();
        let icon = asciiIcons.sun;
        if (description.includes('дожд')) icon = asciiIcons.rain;
        else if (description.includes('снег')) icon = asciiIcons.snow;
        else if (description.includes('облач')) icon = asciiIcons.cloud;
        TerminalApp.printHtml(`<pre style="margin:0;color:#0f0;">${icon}</pre>`);
        TerminalApp.print(`${(data.city || '').toUpperCase()}`, 'big');
        TerminalApp.print(`Температура: ${data.temperature}°C`);
        TerminalApp.print(`Влажность: ${data.humidity}%`);
        TerminalApp.print(`Описание: ${data.description}`);
        if (TerminalApp.getCurrentUser() !== 'guest') {
          TerminalApp.fetchHistory();
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'flight') {
      if (!arg) {
        TerminalApp.print('Error: airport IATA required', 'error');
        return;
      }
      TerminalApp.print(`Fetching flight for ${arg.toUpperCase()}...`);
      try {
        const resp = await fetch(`/api/flight/?airport=${encodeURIComponent(arg)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.printHtml(`<pre style="margin:0;color:#0f0;">${asciiIcons.plane}</pre>`);
        TerminalApp.print(`Рейс: ${data.flight_number}`, 'big');
        TerminalApp.print(`Авиакомпания: ${data.airline}`);
        TerminalApp.print(`Статус: ${data.status}`);
        TerminalApp.print(`Вылет: ${data.departure_airport} @ ${data.departure_time || 'N/A'}`);
        TerminalApp.print(`Прилет: ${data.arrival_airport} @ ${data.arrival_time || 'N/A'}`);
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
      return;
    }

    if (cmd === 'currency') {
      const params = parts.slice(1);
      if (!params.length) {
        TerminalApp.print('Ошибка: используйте currency <из> [в] [сумма]');
        TerminalApp.print('Доступные коды:');
        TerminalApp.CURRENCY_LIST.forEach(([code, name]) => TerminalApp.print(`${code} — ${name}`));
        return;
      }

      const baseUpper = params[0].toUpperCase();
      if (!TerminalApp.CURRENCY_MAP[baseUpper]) {
        TerminalApp.print('Эта валюта не поддерживается. Допустимые коды:');
        TerminalApp.CURRENCY_LIST.forEach(([code, name]) => TerminalApp.print(`${code} — ${name}`));
        return;
      }

      let targetUpper = null;
      let amount = 1;

      if (params.length >= 2) {
        const maybeCode = params[1].toUpperCase();
        if (TerminalApp.CURRENCY_MAP[maybeCode]) {
          if (maybeCode === baseUpper) {
            TerminalApp.print('Выберите валюту, отличную от базовой.');
            return;
          }
          targetUpper = maybeCode;
          if (params.length >= 3) {
            const maybeAmount = Number.parseFloat(params[2].replace(',', '.'));
            if (Number.isFinite(maybeAmount) && maybeAmount > 0) amount = maybeAmount;
          }
        } else {
          const maybeAmount = Number.parseFloat(params[1].replace(',', '.'));
          if (Number.isFinite(maybeAmount) && maybeAmount > 0) amount = maybeAmount;
        }
      }

      if (params.length >= 3 && !targetUpper) {
        const maybeAmount = Number.parseFloat(params[2].replace(',', '.'));
        if (Number.isFinite(maybeAmount) && maybeAmount > 0) amount = maybeAmount;
      }

      const availableCodes = TerminalApp.CURRENCY_LIST.map(([code]) => code).filter((code) => code !== baseUpper);
      const requestCodes = targetUpper ? [targetUpper] : availableCodes;

      if (!requestCodes.length) {
        TerminalApp.print('Нет валют для конвертации.');
        return;
      }

      if (TerminalApp.elements.output) TerminalApp.elements.output.innerHTML = '';

      try {
        const search = new URLSearchParams({ base: baseUpper, symbols: requestCodes.join(',') });
        const resp = await fetch(`/api/currency/?${search.toString()}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Ошибка: ${data.error || resp.statusText}`, 'error');
          return;
        }

        const rates = data.rates || {};
        const entries = requestCodes.map((code) => [code, TerminalApp.CURRENCY_MAP[code], rates[code]]);

        const width = 74;
        const border = `+${'-'.repeat(width - 2)}+`;
        const padLine = (text = '') => {
          const truncated = text.length > width - 4 ? `${text.slice(0, width - 7)}...` : text;
          return `| ${truncated.padEnd(width - 4, ' ')} |`;
        };

        const boxLines = [
          border,
          padLine('КУРСЫ ВАЛЮТ'),
          padLine(`Базовая валюта: ${data.base}`),
          padLine(`Сумма: ${amount}`),
        ];

        if (data.fetched_at) {
          const formatted = TerminalApp.formatHistoryTime(data.fetched_at);
          if (formatted) boxLines.push(padLine(`Обновлено: ${formatted}`));
        }

        boxLines.push(border);
        entries.forEach(([code, name, rate]) => {
          if (typeof rate === 'number') {
            const converted = amount * rate;
            boxLines.push(padLine(`${code} — ${name}; курс: ${rate}; ${amount} ${data.base} = ${converted.toFixed(2)} ${code}`));
          } else {
            boxLines.push(padLine(`${code} — ${name}; курс недоступен`));
          }
        });
        boxLines.push(border);

        TerminalApp.printHtml(`<pre>${boxLines.join('\n')}</pre>`);

        if (!targetUpper) {
          TerminalApp.print(`Подсказка: для конкретной валюты используйте команду вида currency ${baseUpper.toLowerCase()} <код> [сумма]`);
        }
      } catch (err) {
        TerminalApp.print(`Ошибка: ${err.message}`, 'error');
      }
      return;
    }

    TerminalApp.print(`Unknown command: ${cmd}`, 'error');
  };
})();
