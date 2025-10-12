// Pulls admin dashboard statistics for staff users.
(() => {
  const TerminalApp = window.TerminalApp || (window.TerminalApp = {});
  const { buildAsciiTable, normalizeCellValue } = TerminalApp.utils || {};

  const formatTime = (value) => {
    if (!value) return '-';
    const formatted = TerminalApp.formatHistoryTime ? TerminalApp.formatHistoryTime(value) : null;
    return formatted || value;
  };

  const shorten = (text, limit = 32) => {
    const base = normalizeCellValue ? normalizeCellValue(text) : String(text || '');
    return base.length > limit ? `${base.slice(0, limit - 3)}...` : base;
  };

  TerminalApp.registerCommand('admin', {
    helpEntry: 'admin — сводка по пользователям и задачам (требуются права)',
    execute: async () => {
      TerminalApp.print('Загрузка админской сводки...');
      try {
        const resp = await fetch('/api/admin/overview/', { credentials: 'same-origin' });
        const data = await resp.json();
        if (!resp.ok || data.error) {
          const message = (data && data.error) || resp.statusText || 'Сервис недоступен';
          TerminalApp.print(`Error: ${message}`, 'error');
          return;
        }

        if (buildAsciiTable) {
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
            normalizeCellValue ? normalizeCellValue(user.username || '-') : (user.username || '-'),
            user.is_staff ? 'staff' : '-',
            formatTime(user.date_joined),
            formatTime(user.last_login),
            String(user.tasks_count ?? 0),
            String(user.searches_count ?? 0),
          ]);
          if (usersRows.length) {
            TerminalApp.printHtml(`<pre>${buildAsciiTable(['Пользователь', 'Роль', 'Регистрация', 'Последний логин', 'Задачи', 'Поиски'], usersRows)}</pre>`);
          } else {
            TerminalApp.print('Данные по пользователям отсутствуют.');
          }

          const tasksRows = (data.recent_tasks || []).map((task) => [
            String(task.id),
            normalizeCellValue ? normalizeCellValue(task.user || '-') : (task.user || '-'),
            normalizeCellValue ? normalizeCellValue(task.city || '-') : (task.city || '-'),
            shorten(task.text || ''),
            formatTime(task.created_at),
          ]);
          if (tasksRows.length) {
            TerminalApp.printHtml(`<pre>${buildAsciiTable(['ID', 'Пользователь', 'Город', 'Описание', 'Создано'], tasksRows)}</pre>`);
          } else {
            TerminalApp.print('Недавних задач нет.');
          }

          const searchesRows = (data.recent_searches || []).map((item) => [
            normalizeCellValue ? normalizeCellValue(item.user || '-') : (item.user || '-'),
            normalizeCellValue ? normalizeCellValue(item.city || '-') : (item.city || '-'),
            formatTime(item.created_at),
          ]);
          if (searchesRows.length) {
            TerminalApp.printHtml(`<pre>${buildAsciiTable(['Пользователь', 'Город', 'Когда'], searchesRows)}</pre>`);
          } else {
            TerminalApp.print('История поисков пуста.');
          }
        }
      } catch (err) {
        TerminalApp.print(`Error: ${err.message}`, 'error');
      }
    },
  });
})();
