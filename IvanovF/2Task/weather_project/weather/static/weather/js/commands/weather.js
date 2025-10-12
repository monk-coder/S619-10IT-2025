(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('weather', {
    helpEntry: 'weather <город> — узнать погоду',
    requiresArgs: true,
    execute: async ({ args }) => {
      if (!args) {
        TerminalApp.print('Error: city required', 'error');
        return;
      }
      TerminalApp.print(`Fetching weather for ${args}...`);
      try {
        const resp = await fetch(`/api/weather/?city=${encodeURIComponent(args)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        const description = (data.description || '').toLowerCase();
        let icon = TerminalApp.asciiIcons.sun;
        if (description.includes('дожд')) icon = TerminalApp.asciiIcons.rain;
        else if (description.includes('снег')) icon = TerminalApp.asciiIcons.snow;
        else if (description.includes('облач')) icon = TerminalApp.asciiIcons.cloud;
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
    },
  });
})();
