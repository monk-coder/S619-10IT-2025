(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const AGE_PROMPT = [
    '+-------------+',
    '|  CASINO 18+ |',
    '| Enter age   |',
    '|  q - exit   |',
    '+-------------+',
  ].join('\n');

  const pad = (value, width) => {
    const text = String(value);
    if (text.length >= width) return text.substring(0, width);
    return text + ' '.repeat(width - text.length);
  };

  const buildMenu = (state) => [
    '+----------------------+',
    '| Age    : ' + pad(state.ageValue ?? '--', 8) + '|',
    '| Balance: ' + pad(state.balance, 8) + '|',
    '| Stake  : ' + pad(state.stake, 8) + '|',
    '|----------------------|',
    '| 1 - slots            |',
    '| 2 - roulette         |',
    '| q - exit             |',
    '+----------------------+',
  ].join('\n');

  const SLOT_ART = (digits, balance, stake) => [
    '###############',
    '#  SLOT GAME  #',
    '#-------------#',
    '# ' + digits[0] + ' | ' + digits[1] + ' | ' + digits[2] + ' #',
    '#-------------#',
    '# Balance: ' + pad(balance, 5) + '#',
    '# Stake  : ' + pad(stake, 5) + '#',
    '###############',
  ].join('\n');

  const ROULETTE_ART = (roll, color, balance, stake) => [
    '====================',
    '|   MINI ROULETTE  |',
    '====================',
    '| Number: ' + pad(String(roll), 8) + '|',
    '| Color : ' + pad(color, 8) + '|',
    '| Balance: ' + pad(balance, 8) + '|',
    '| Stake  : ' + pad(stake, 8) + '|',
    '====================',
  ].join('\n');

  const getCasinoState = () => (TerminalApp.state && TerminalApp.state.casino ? TerminalApp.state.casino : null);

  const ensureSession = () => {
    if (!TerminalApp.__casinoSession) {
      TerminalApp.__casinoSession = { stage: null, mode: null, lastBet: null };
    }
    return TerminalApp.__casinoSession;
  };

  const clearFlags = () => {
    TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(false);
    TerminalApp.setCasinoAwaitingMode && TerminalApp.setCasinoAwaitingMode(false);
    TerminalApp.setCasinoAwaitingSpin && TerminalApp.setCasinoAwaitingSpin(false);
    TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(false);
    TerminalApp.clearCasinoPendingMode && TerminalApp.clearCasinoPendingMode();
  };

  const exitCasino = (message = 'You left the casino.') => {
    clearFlags();
    TerminalApp.__casinoSession = null;
    if (message) TerminalApp.print(message);
  };

  const showAgePrompt = () => {
    const session = ensureSession();
    clearFlags();
    session.stage = 'age';
    TerminalApp.setCasinoAwaitingAge && TerminalApp.setCasinoAwaitingAge(true);
    TerminalApp.printHtml('<pre>' + AGE_PROMPT + '</pre>');
    TerminalApp.print('Enter your age as a number (q - exit).');
  };

  const showMenu = () => {
    const session = ensureSession();
    const state = getCasinoState();
    if (!state) return;
    clearFlags();
    session.stage = 'menu';
    TerminalApp.setCasinoAwaitingMode && TerminalApp.setCasinoAwaitingMode(true);
    TerminalApp.printHtml('<pre>' + buildMenu(state) + '</pre>');
    TerminalApp.print('Choose: 1 - slots, 2 - roulette, q - exit.');
  };

  const takeStake = (stake) => {
    const state = getCasinoState();
    if (!state) return false;
    if (state.balance < stake) {
      TerminalApp.print('Not enough balance for stake ' + stake + '.');
      showMenu();
      return false;
    }
    TerminalApp.adjustCasinoBalance && TerminalApp.adjustCasinoBalance(-stake);
    return true;
  };

  const askAgain = (mode, bet = null) => {
    const session = ensureSession();
    session.stage = 'again';
    session.mode = mode;
    session.lastBet = bet;
    TerminalApp.setCasinoAwaitingReplay && TerminalApp.setCasinoAwaitingReplay(true, mode);
    TerminalApp.print('Play again? (y=yes, m=menu, n/q=exit)');
  };

  const playSlots = () => {
    const state = getCasinoState();
    if (!state) return;
    const stake = state.stake || 10;
    if (!takeStake(stake)) return;

    const digits = [0, 0, 0].map(() => Math.floor(Math.random() * 10));
    let win = 0;
    if (digits[0] === digits[1] && digits[1] === digits[2]) {
      win = stake * 5;
    } else if (digits[0] === digits[1] || digits[1] === digits[2] || digits[0] === digits[2]) {
      win = stake * 2;
    }
    if (win > 0) TerminalApp.adjustCasinoBalance && TerminalApp.adjustCasinoBalance(win);

    const balance = getCasinoState().balance;
    TerminalApp.printHtml('<pre>' + SLOT_ART(digits, balance, stake) + '</pre>');
    TerminalApp.print(win > 0 ? 'You won ' + win + '!' : 'You lost ' + stake + '.');
    askAgain('slots');
  };

  const parseRouletteBet = (input) => {
    if (/^\d+$/.test(input)) {
      const value = Number(input);
      if (value >= 0 && value <= 36) return { type: 'number', value };
    }
    const colors = { red: 'RED', black: 'BLACK', green: 'GREEN' };
    if (colors[input]) return { type: 'color', value: colors[input] };
    const parity = { odd: 'odd', even: 'even' };
    if (parity[input]) return { type: 'parity', value: parity[input] };
    return null;
  };

  const colorName = (key) => (key === 'RED' ? 'RED' : key === 'BLACK' ? 'BLACK' : 'GREEN');

  const playRoulette = (bet) => {
    const state = getCasinoState();
    if (!state) return;
    const stake = state.stake || 10;
    if (!takeStake(stake)) return;

    const roll = Math.floor(Math.random() * 37);
    const colorKey = roll === 0 ? 'GREEN' : (roll % 2 === 0 ? 'RED' : 'BLACK');
    const parityKey = roll === 0 ? null : (roll % 2 === 0 ? 'even' : 'odd');

    let win = 0;
    if (bet.type === 'number' && bet.value === roll) win = stake * 10;
    if (bet.type === 'color' && bet.value === colorKey) win = stake * 2;
    if (bet.type === 'parity' && bet.value === parityKey) win = stake * 2;
    if (win > 0) TerminalApp.adjustCasinoBalance && TerminalApp.adjustCasinoBalance(win);

    const balance = getCasinoState().balance;
    TerminalApp.printHtml('<pre>' + ROULETTE_ART(roll, colorName(colorKey), balance, stake) + '</pre>');
    TerminalApp.print(win > 0 ? 'You won ' + win + '.' : 'You lost ' + stake + '.');
    askAgain('roulette', bet);
  };

  const handleAge = (input) => {
    const age = Number(input.replace(',', '.'));
    if (!Number.isFinite(age)) {
      TerminalApp.print('Please enter a number.');
      return;
    }
    if (Math.floor(age) < 18) {
      exitCasino('Only players 18+ can enter.');
      return;
    }
    TerminalApp.confirmCasinoAge && TerminalApp.confirmCasinoAge(age);
    TerminalApp.print('Age ' + Math.floor(age) + ' accepted.');
    showMenu();
  };

  const handleMenu = (input) => {
    if (['1', 'slots', 'slot'].includes(input)) {
      playSlots();
      return;
    }
    if (['2', 'roulette'].includes(input)) {
      const session = ensureSession();
      clearFlags();
      session.stage = 'rouletteBet';
      TerminalApp.print('Type bet: number 0-36, or red/black/green, or odd/even.');
      return;
    }
    TerminalApp.print('Choose 1, 2 or q.');
  };

  const handleRouletteBet = (input) => {
    const bet = parseRouletteBet(input);
    if (!bet) {
      TerminalApp.print('Bet not understood, try again.');
      return;
    }
    playRoulette(bet);
  };

  const handleAgain = (input) => {
    const session = ensureSession();
    if (['y', 'yes'].includes(input)) {
      if (session.mode === 'slots') {
        playSlots();
      } else {
        session.stage = 'rouletteBet';
        TerminalApp.print('Type a roulette bet (number/color/odd/even).');
      }
      return;
    }
    if (['m', 'menu'].includes(input)) {
      showMenu();
      return;
    }
    exitCasino('Game finished.');
  };

  TerminalApp.registerInterceptor((context) => {
    const session = TerminalApp.__casinoSession;
    if (!session || !session.stage) return false;

    const inputRaw = context.trimmed.trim();
    const input = inputRaw.toLowerCase();

    if (context.command && context.command !== 'casino') {
      exitCasino();
      return false;
    }

    if (!input) {
      context.stop();
      return true;
    }

    if (input === 'q') {
      exitCasino();
      context.stop();
      return true;
    }

    const handlers = {
      age: handleAge,
      menu: handleMenu,
      rouletteBet: handleRouletteBet,
      again: handleAgain,
    };

    const handler = handlers[session.stage];
    if (handler) handler(inputRaw);
    context.stop();
    return true;
  });

  TerminalApp.registerCommand('casino', {
    helpEntry: 'casino - simple games (q exits)',
    execute: ({ parts }) => {
      const state = getCasinoState();
      if (!state) {
        TerminalApp.print('Casino data missing.');
        return;
      }

      const session = ensureSession();
      const sub = (parts[1] || '').toLowerCase();

      if (sub === 'reset') {
        const value = TerminalApp.resetCasinoBalance ? TerminalApp.resetCasinoBalance() : state.initialBalance;
        TerminalApp.print('Balance restored to ' + value + '.');
        return;
      }

      if (sub === 'stake') {
        const raw = parts[2];
        const next = Number(raw);
        if (!raw || !Number.isFinite(next) || next <= 0) {
          TerminalApp.print('Usage: casino stake 25');
        } else {
          TerminalApp.setCasinoStake && TerminalApp.setCasinoStake(next);
          TerminalApp.print('Stake set to ' + TerminalApp.getCasinoStake() + '.');
        }
        return;
      }

      if (sub === 'status') {
        const ageLabel = state.ageConfirmed ? state.ageValue : 'not confirmed';
        TerminalApp.print('Balance: ' + state.balance + '; Stake: ' + state.stake + '; Age: ' + ageLabel + '.');
        return;
      }

      if (sub === 'help') {
        TerminalApp.print('casino - start games');
        TerminalApp.print('casino stake N - change stake');
        TerminalApp.print('casino reset - restore balance');
        TerminalApp.print('casino status - current info');
        TerminalApp.print('Inside the game use q to leave.');
        return;
      }

      if (session.stage) {
        showMenu();
        return;
      }

      if (TerminalApp.isCasinoAgeConfirmed && TerminalApp.isCasinoAgeConfirmed()) {
        showMenu();
      } else {
        showAgePrompt();
      }
    },
  });
})();

