(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('flight', {
    helpEntry: 'flight <IATA> — статус рейса',
    requiresArgs: true,
    execute: async ({ args }) => {
      if (!args) {
        TerminalApp.print('Error: airport IATA required', 'error');
        return;
      }
      TerminalApp.print(`Fetching flight for ${args.toUpperCase()}...`);
      try {
        const resp = await fetch(`/api/flight/?airport=${encodeURIComponent(args)}`);
        const data = await resp.json();
        if (!resp.ok || data.error) {
          TerminalApp.print(`Error: ${data.error || resp.statusText}`, 'error');
          return;
        }
        TerminalApp.printHtml(`<pre style="margin:0;color:#0f0;">${TerminalApp.asciiIcons.plane}</pre>`);
        TerminalApp.print(`Рейс: ${data.flight_number}`, 'big');
        TerminalApp.print(`Авиакомпания: ${data.airline}`);
        TerminalApp.print(`Статус: ${data.status}`);
        TerminalApp.print(`Вылет: ${data.departure_airport} @ ${data.departure_time || 'N/A'}`);
        TerminalApp.print(`Прилет: ${data.arrival_airport} @ ${data.arrival_time || 'N/A'}`);
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
    },
  });
})();
