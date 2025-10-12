(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  if (!TerminalApp.CURRENCY_LIST) {
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
  }

  const listCurrencies = () => {
    TerminalApp.print('Доступные коды:');
    TerminalApp.CURRENCY_LIST.forEach(([code, name]) => TerminalApp.print(`${code} — ${name}`));
  };

  TerminalApp.registerCommand('currency', {
    helpEntry: 'currency <из> [в] [сумма] — конвертация валют из списка (например: currency usd rub 100)',
    requiresArgs: true,
    execute: async ({ parts }) => {
      const params = parts.slice(1);
      if (!params.length) {
        TerminalApp.print('Ошибка: используйте currency <из> [в] [сумма]');
        listCurrencies();
        return;
      }

      const baseUpper = params[0].toUpperCase();
      if (!TerminalApp.CURRENCY_MAP[baseUpper]) {
        TerminalApp.print('Эта валюта не поддерживается. Допустимые коды:');
        listCurrencies();
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
    },
  });
})();
