(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});

  TerminalApp.registerCommand('fetch', {
    helpEntry: 'fetch — вывести информацию о системе',
    execute: () => {
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
    },
  });
})();
