// Core terminal wiring that keeps registry of commands, interceptors and autocomplete hints.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  const commandRegistry = new Map();
  const commandNames = [];
  const aliasRegistry = new Map();
  const interceptors = [];
  const helpItems = [];
  const commandsWithArgs = new Set();

  const asciiIcons = {
    sun: '  \\   /  \n   .-.   \n- (   ) -\n   `-’   \n  /   \\  ',
    cloud: '    .--.   \n .-(    ). \n(___.__)__)',
    rain: '    .--.   \n .-(    ). \n(___.__)__)\n \' \' \' \' \' ',
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
      '      /#######/       \\\\#######\\',
      '     /########         ########\\',
      '    /#########         ######m=,_',
      '   /##########         ##########\\',
      '  /######***             ***######\\',
      ' /###**                       **###\\',
      '/**                               **\\',
    ].join('\n'),
  };

  TerminalApp.asciiIcons = asciiIcons;
  TerminalApp.helpItems = helpItems;

  const registerHelpEntry = (entry) => {
    if (!entry) return;
    if (Array.isArray(entry)) {
      entry.forEach(registerHelpEntry);
      return;
    }
    helpItems.push(String(entry));
  };

  const registerAlias = (alias, target) => {
    if (!alias || !target) return;
    const normalizedAlias = String(alias).trim().toLowerCase();
    if (!normalizedAlias || commandRegistry.has(normalizedAlias)) return;
    aliasRegistry.set(normalizedAlias, target);
  };

  TerminalApp.registerAlias = registerAlias;

  // Entry-point used by command modules to register themselves with the shell.
  TerminalApp.registerCommand = (name, options = {}) => {
    const commandName = String(name || '').trim().toLowerCase();
    if (!commandName) {
      throw new Error('Command name is required');
    }
    if (commandRegistry.has(commandName)) {
      throw new Error(`Command ${commandName} is already registered`);
    }

    const {
      execute,
      description = '',
      usage = '',
      aliases = [],
      helpEntry = null,
      requiresArgs = false,
    } = options;

    if (typeof execute !== 'function') {
      throw new Error(`Command ${commandName} must provide an execute() function`);
    }

    const meta = {
      name: commandName,
      execute,
      description,
      usage,
      aliases: Array.isArray(aliases) ? aliases.slice() : [],
      helpEntry,
      requiresArgs: Boolean(requiresArgs),
    };

    commandRegistry.set(commandName, meta);
    commandNames.push(commandName);
    if (helpEntry) registerHelpEntry(helpEntry);
    if (meta.requiresArgs) commandsWithArgs.add(commandName);

    meta.aliases.forEach((alias) => registerAlias(alias, commandName));
    if (typeof TerminalApp.refreshAutocompleteHint === 'function') {
      TerminalApp.refreshAutocompleteHint();
    }
    return meta;
  };

  TerminalApp.getCommandNames = () => commandNames.slice();
  TerminalApp.getCommandDefinition = (name) => commandRegistry.get(name);
  TerminalApp.registerHelpEntry = registerHelpEntry;

  // Interceptors run before regular commands to support multi-step flows.
  TerminalApp.registerInterceptor = (interceptor) => {
    if (typeof interceptor !== 'function') {
      throw new Error('Interceptor must be a function');
    }
    interceptors.push(interceptor);
    return () => {
      const idx = interceptors.indexOf(interceptor);
      if (idx >= 0) interceptors.splice(idx, 1);
    };
  };

  const normalizeCellValue = (value) => {
    if (value === null || value === undefined) return '';
    return String(value).replace(/\s+/g, ' ').trim();
  };

  const buildAsciiTable = (headers, rows) => {
    if (!headers || !headers.length) return '';
    const processedRows = rows.map((row) => headers.map((_, idx) => normalizeCellValue(row[idx])));
    const widths = headers.map((header, idx) => {
      const cellLengths = processedRows.map((row) => (row[idx] ? row[idx].length : 0));
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

  const escapeHtml = (text) => String(text).replace(/[&<>"']/g, (ch) => {
    switch (ch) {
      case '&':
        return '&amp;';
      case '<':
        return '&lt;';
      case '>':
        return '&gt;';
      case '"':
        return '&quot;';
      case '\'':
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

  const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  const isYesResponse = (value) => {
    const entry = (value || '').trim().toLowerCase();
    return ['y', 'yes', 'yeah', 'да', 'д', 'угу', 'ага'].includes(entry);
  };

  const isNoResponse = (value) => {
    const entry = (value || '').trim().toLowerCase();
    return ['n', 'no', 'нет', 'н', 'неа'].includes(entry);
  };

  TerminalApp.utils = Object.assign(TerminalApp.utils || {}, {
    normalizeCellValue,
    buildAsciiTable,
    escapeHtml,
    getCommonPrefix,
    sleep,
    isYesResponse,
    isNoResponse,
  });

  const createContext = (rawValue) => {
    const raw = typeof rawValue === 'string' ? rawValue : '';
    const trimmed = raw.trim();
    const parts = trimmed.length ? trimmed.split(/\s+/) : [];
    return {
      raw,
      trimmed,
      parts,
      command: parts[0] ? parts[0].toLowerCase() : '',
      args: parts.slice(1).join(' '),
      handled: false,
      stop() {
        this.handled = true;
      },
      replaceParts(newParts) {
        this.parts = Array.isArray(newParts) ? newParts : [];
        this.command = this.parts[0] ? this.parts[0].toLowerCase() : '';
        this.args = this.parts.slice(1).join(' ');
      },
      setCommand(name) {
        this.command = (name || '').toLowerCase();
      },
      setArgs(args) {
        this.args = typeof args === 'string' ? args : '';
      },
    };
  };

  // Dispatcher that runs interceptors first and falls back to registered commands.
  TerminalApp.executeCommand = async (rawValue) => {
    const context = createContext(rawValue);
    if (!context.parts.length) return;

    for (const interceptor of interceptors) {
      const result = await interceptor(context);
      if (context.handled || result === true) {
        return;
      }
    }

    if (!context.parts.length) return;

    let { command } = context;
    const { args, raw, trimmed, parts } = context;

    if (!command) {
      return;
    }

    if (!commandRegistry.has(command) && aliasRegistry.has(command)) {
      command = aliasRegistry.get(command);
    }

    const handler = commandRegistry.get(command);
    if (!handler) {
      TerminalApp.print(`Unknown command: ${context.command || command}`, 'error');
      return;
    }

    await handler.execute({
      raw,
      trimmed,
      parts: parts.slice(),
      args,
      command,
      originalCommand: context.command,
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

    const matches = commandNames.filter((cmd) => cmd.startsWith(partialLower));
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

  TerminalApp.computeAutocompleteSuggestion = computeAutocompleteSuggestion;

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
    hint.innerHTML = `<span class='ghost-hidden'>${escapeHtml(suggestion.beforeCaret)}</span>${escapeHtml(suggestion.completion)}`;
  };

  // Replaces current input with the best-matching command suggestion.
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

  // Default help output that collects descriptions contributed by modules.
  TerminalApp.showHelp = () => {
    TerminalApp.print('Добро пожаловать в терминал погоды и рейсов');
    TerminalApp.printHtml('<span class=\'big\'>Терминальный дашборд</span>');
    TerminalApp.print('Доступные команды:');
    helpItems.forEach((entry) => TerminalApp.print(`- ${entry}`));
    TerminalApp.print('Подсказка: команда timezone принимает значения вроде +3 или -5.5');
  };
})();
