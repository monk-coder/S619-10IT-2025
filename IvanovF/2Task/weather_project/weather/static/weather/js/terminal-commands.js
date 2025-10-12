// Ядро терминала: регистрируем команды, перехватчики, авто-дополнение и справку.
(function () {
  var TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.commands = TerminalApp.commands || {};
  TerminalApp.commandNames = TerminalApp.commandNames || [];
  TerminalApp.aliases = TerminalApp.aliases || {};
  TerminalApp.interceptors = TerminalApp.interceptors || [];
  TerminalApp.helpItems = TerminalApp.helpItems || [];
  TerminalApp.commandsWithArgs = TerminalApp.commandsWithArgs || [];

  // Примитивные псевдо-иконки на случай вывода погоды и рейсов.
  // Команды просто берут нужную строку по ключу и вставляют в <pre>.
  TerminalApp.asciiIcons = {
    sun: [
      "    \\\\   /",
      "     .-.",
      "  ― (   ) ―",
      "     `-`",
      "    /   \\\\"
    ].join("\n"),
    cloud: [
      "      .--.",
      "   .-(    ).",
      "  (___.__)__)"
    ].join("\n"),
    rain: [
      "      .--.",
      "   .-(    ).",
      "  (___.__)__)",
      "   ' ' ' ' '"
    ].join("\n"),
    snow: [
      "      .--.",
      "   .-(    ).",
      "  (___.__)__)",
      "   *  *  *  *"
    ].join("\n"),
    plane: [
      "        __|__",
      " --@--@--(_)--@--@--"
    ].join("\n"),
    arch: [
      "                 /#\\\\",
      "                /###\\\\",
      "               /#####\\\\",
      "              /#######\\\\",
      "             _ \"=######\\\\",
      "            /##=,_\\\\#####\\\\",
      "           /#############\\\\",
      "          /###############\\\\",
      "         /#################\\\\",
      "        /###################\\\\",
      "       /########*\"\"\"*########\\\\",
      "      /#######/       \\\\#######\\\\",
      "     /########         ########\\\\",
      "    /#########         ######m=,_",
      "   /##########         ##########\\\\",
      "  /######***             ***######\\\\",
      " /###**                       **###\\\\",
      "/**                               **\\\\"
    ].join("\n")
  };

  // Делает ячейку таблицы аккуратной строкой.
  function normalizeCellValue(value) {
    if (value === null || value === undefined) {
      return "";
    }
    return String(value).replace(/\s+/g, " ").trim();
  }

  // Строит простую ASCII-таблицу из заголовков и строк.
  function buildAsciiTable(headers, rows) {
    if (!headers || !headers.length) {
      return "";
    }
    // Проходим по строкам и нормализуем каждую ячейку, чтобы избавиться от лишних пробелов.
    var processedRows = rows.map(function (row) {
      return headers.map(function (_, idx) {
        return normalizeCellValue(row[idx]);
      });
    });

    // Для каждой колонки вычисляем максимально возможную ширину.
    var widths = headers.map(function (header, idx) {
      var length = header.length;
      processedRows.forEach(function (row) {
        if (row[idx] && row[idx].length > length) {
          length = row[idx].length;
        }
      });
      return Math.max(length, 3);
    });

    // Горизонтальная рамка вокруг таблицы.
    var border = "+" + widths.map(function (w) {
      return Array(w + 3).join("-");
    }).join("+") + "+";

    function formatLine(cells) {
      return "|" + cells.map(function (cell, idx) {
        return " " + (cell || "").padEnd(widths[idx], " ") + " ";
      }).join("|") + "|";
    }

    var lines = [border, formatLine(headers), border];
    if (!processedRows.length) {
      lines.push(formatLine(headers.map(function () {
        return "\u2014";
      })));
    } else {
      processedRows.forEach(function (row) {
        lines.push(formatLine(row));
      });
    }
    lines.push(border);
    return lines.join("\n");
  }

  // Экранирует HTML, чтобы подсказки не ломали разметку.
  function escapeHtml(text) {
    return String(text).replace(/[&<>"']/g, function (ch) {
      switch (ch) {
        case "&": return "&amp;";
        case "<": return "&lt;";
        case ">": return "&gt;";
        case "\"": return "&quot;";
        case "'": return "&#39;";
        default: return ch;
      }
    });
  }

  // Простая задержка с использованием Promise.
  function sleep(ms) {
    return new Promise(function (resolve) {
      setTimeout(resolve, ms);
    });
  }

  // Проверяем, что ответ похож на "да".
  function isYesResponse(value) {
    var entry = (value || "").trim().toLowerCase();
    return ["y", "yes", "yeah", "да", "д", "угу", "ага"].indexOf(entry) >= 0;
  }

  // Проверяем, что ответ похож на "нет".
  function isNoResponse(value) {
    var entry = (value || "").trim().toLowerCase();
    return ["n", "no", "нет", "н", "неа"].indexOf(entry) >= 0;
  }

  // Экспортируем утилиты, чтобы ими могли пользоваться команды (например, admin).
  TerminalApp.utils = TerminalApp.utils || {};
  TerminalApp.utils.normalizeCellValue = normalizeCellValue;
  TerminalApp.utils.buildAsciiTable = buildAsciiTable;
  TerminalApp.utils.escapeHtml = escapeHtml;
  TerminalApp.utils.sleep = sleep;
  TerminalApp.utils.isYesResponse = isYesResponse;
  TerminalApp.utils.isNoResponse = isNoResponse;

  // Добавляем пункты в раздел помощи.
  function addHelpEntry(entry) {
    if (!entry) {
      return;
    }
    if (Array.isArray(entry)) {
      entry.forEach(addHelpEntry);
    } else {
      TerminalApp.helpItems.push(String(entry));
    }
  }

  // Регистрируем короткое имя команды.
  function addAlias(alias, target) {
    if (!alias || !target) {
      return;
    }
    var name = String(alias).trim().toLowerCase();
    if (!name || TerminalApp.commands[name]) {
      return;
    }
    TerminalApp.aliases[name] = target;
  }

  TerminalApp.registerAlias = addAlias;

  // Основной реестр команд терминала.
  TerminalApp.registerCommand = function (name, options) {
    options = options || {};
    var commandName = String(name || "").trim().toLowerCase();
    if (!commandName) {
      throw new Error("Command name is required");
    }
    if (TerminalApp.commands[commandName]) {
      throw new Error("Command " + commandName + " already exists");
    }
    if (typeof options.execute !== "function") {
      throw new Error("Command " + commandName + " must have execute function");
    }

    // Сохраняем основную структуру с обработчиком и метаданными.
    TerminalApp.commands[commandName] = {
      name: commandName,
      execute: options.execute,
      helpEntry: options.helpEntry || null,
      requiresArgs: !!options.requiresArgs,
      aliases: Array.isArray(options.aliases) ? options.aliases.slice() : []
    };

    // Массива команд используется для автодополнения.
    TerminalApp.commandNames.push(commandName);

    if (options.helpEntry) {
      addHelpEntry(options.helpEntry);
    }
    if (TerminalApp.commands[commandName].requiresArgs) {
      TerminalApp.commandsWithArgs.push(commandName);
    }
    // Регистрируем синонимы, чтобы их можно было найти до выполнения.
    TerminalApp.commands[commandName].aliases.forEach(function (alias) {
      addAlias(alias, commandName);
    });
  };

  TerminalApp.registerHelpEntry = addHelpEntry;

  // Многошаговые команды могут ставить перехватчики ввода.
  TerminalApp.registerInterceptor = function (fn) {
    if (typeof fn !== "function") {
      throw new Error("Interceptor must be a function");
    }
    TerminalApp.interceptors.push(fn);
    return function () {
      var index = TerminalApp.interceptors.indexOf(fn);
      if (index >= 0) {
        TerminalApp.interceptors.splice(index, 1);
      }
    };
  };

  // Подбираем общую часть строк для автодополнения.
  function getCommonPrefix(items) {
    if (!items.length) {
      return "";
    }
    var first = items[0];
    for (var i = 0; i < first.length; i += 1) {
      var ch = first[i];
      for (var j = 1; j < items.length; j += 1) {
        if (items[j][i] !== ch) {
          return first.slice(0, i);
        }
      }
    }
    return first;
  }

  // Разбираем введённую строку на команду и аргументы.
  function createContext(rawValue) {
    var raw = typeof rawValue === "string" ? rawValue : "";
    var trimmed = raw.trim();
    var parts = trimmed ? trimmed.split(/\s+/) : [];
    return {
      raw: raw,
      trimmed: trimmed,
      parts: parts,
      command: parts[0] ? parts[0].toLowerCase() : "",
      args: parts.slice(1).join(" "),
      handled: false,
      stop: function () {
        this.handled = true;
      }
    };
  }

  // Выполняем команду с учётом всех перехватчиков.
  TerminalApp.executeCommand = async function (rawValue) {
    var context = createContext(rawValue);
    if (!context.parts.length) {
      return;
    }

    // Сначала даём шанс перехватчикам (например, казино) обработать ввод.
    for (var i = 0; i < TerminalApp.interceptors.length; i += 1) {
      var interceptor = TerminalApp.interceptors[i];
      /* eslint-disable no-await-in-loop */
      var result = await interceptor(context);
      /* eslint-enable no-await-in-loop */
      if (context.handled || result === true) {
        return;
      }
    }

    if (!context.parts.length) {
      return;
    }

    // Если команда зарегистрирована как алиас, подменяем имя.
    var name = context.command;
    if (!TerminalApp.commands[name] && TerminalApp.aliases[name]) {
      name = TerminalApp.aliases[name];
      context.command = name;
    }

    var handler = TerminalApp.commands[name];
    if (!handler) {
      TerminalApp.print("Unknown command: " + (context.command || name), "error");
      return;
    }

    // Передаём обработчику полные сведения о вводе.
    await handler.execute({
      raw: context.raw,
      trimmed: context.trimmed,
      parts: context.parts.slice(),
      args: context.args,
      command: name,
      originalCommand: context.parts[0]
    });
  };

  // Подсказываем, чем можно дополнить набранную команду.
  function computeAutocompleteSuggestion() {
    var input = TerminalApp.elements && TerminalApp.elements.input;
    if (!input) {
      return null;
    }

    var value = input.value || "";
    var caret = input.selectionStart == null ? value.length : input.selectionStart;
    if (caret !== value.length) {
      return null;
    }

    var beforeCaret = value.slice(0, caret);
    if (!beforeCaret.trim() || beforeCaret.indexOf(" ") >= 0) {
      return null;
    }

    var partial = beforeCaret.trim().toLowerCase();
    // Получаем список команд, которые начинаются с введённого префикса.
    var matches = TerminalApp.commandNames.filter(function (name) {
      return name.indexOf(partial) === 0;
    });

    if (!matches.length) {
      return null;
    }

    var unique = matches.length === 1;
    var target = null;
    if (unique) {
      target = matches[0];
      if (TerminalApp.commandsWithArgs.indexOf(target) >= 0 && !value.endsWith(" ")) {
        target += " ";
      }
    } else {
      var common = getCommonPrefix(matches);
      if (common.length > partial.length) {
        target = common;
      }
    }

    if (!target) {
      return {
        beforeCaret: beforeCaret,
        matches: matches,
        unique: unique,
        completion: "",
        target: null
      };
    }

    return {
      beforeCaret: beforeCaret,
      matches: matches,
      unique: unique,
      completion: target.slice(partial.length),
      target: target
    };
  }

  TerminalApp.computeAutocompleteSuggestion = computeAutocompleteSuggestion;

  // Перерисовываем прозрачную подсказку справа от курсора.
  TerminalApp.refreshAutocompleteHint = function () {
    var hint = TerminalApp.elements && TerminalApp.elements.hint;
    var input = TerminalApp.elements && TerminalApp.elements.input;
    if (!hint || !input) {
      return;
    }

    var suggestion = computeAutocompleteSuggestion();
    if (!suggestion || !suggestion.completion || !suggestion.completion.trim()) {
      hint.textContent = "";
      if (hint.style) {
        hint.style.transform = "translateY(-50%)";
      }
      return;
    }

    var scrollLeft = input.scrollLeft || 0;
    hint.style.transform = "translate(" + (-scrollLeft) + "px, -50%)";
    // Внутри ghost-hidden отображаем уже введённую часть для правильного выравнивания.
    hint.innerHTML = "<span class=\"ghost-hidden\">" + escapeHtml(suggestion.beforeCaret) + "</span>" + escapeHtml(suggestion.completion);
  };

  // Вставляем подсказку в поле ввода.
  TerminalApp.autocompleteCommand = function () {
    var input = TerminalApp.elements && TerminalApp.elements.input;
    if (!input) {
      return;
    }

    var suggestion = computeAutocompleteSuggestion();
    if (!suggestion) {
      return;
    }

    if (suggestion.target) {
      var caret = input.selectionStart == null ? input.value.length : input.selectionStart;
      var rest = input.value.slice(caret);
      input.value = suggestion.target + rest;
      var pos = suggestion.target.length;
      input.setSelectionRange(pos, pos);
      setTimeout(function () {
        if (TerminalApp.updateCursorPosition) {
          TerminalApp.updateCursorPosition();
        }
        TerminalApp.refreshAutocompleteHint();
      });
      if (!suggestion.unique && suggestion.matches && suggestion.matches.length > 1) {
        // Если вариантов несколько, выводим подсказку в консоль терминала.
        TerminalApp.print("Suggestions: " + suggestion.matches.join("  "));
      }
      return;
    }

    if (suggestion.matches && suggestion.matches.length > 1) {
      TerminalApp.print("Suggestions: " + suggestion.matches.join("  "));
    }
    TerminalApp.refreshAutocompleteHint();
  };

  // Показываем краткую справку по всем командам.
  TerminalApp.showHelp = function () {
    TerminalApp.print("Добро пожаловать в терминал погоды и рейсов");
    TerminalApp.printHtml("<span class=\"big\">Терминальный дашборд</span>");
    TerminalApp.print("Доступные команды:");
    TerminalApp.helpItems.forEach(function (entry) {
      TerminalApp.print("- " + entry);
    });
    TerminalApp.print("Подсказка: команда timezone принимает значения вроде +3 или -5.5");
  };
})();
