document.addEventListener('DOMContentLoaded', function() {
    // Табы
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.getAttribute('data-tab');
            
            // Убираем активные классы
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            // Добавляем активные классы
            this.classList.add('active');
            document.getElementById(`${tabName}-tab`).classList.add('active');
            
            // Если открыли вишлист - обновляем его
            if (tabName === 'wishlist') {
                Wishlist.render();
            }
        });
    });
    
    // Поиск
    // В обработчике поиска замени на:
document.getElementById('searchForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const query = document.getElementById('searchInput').value.trim();
    
    if (query) {
        CountrySearch.showLoading();
        
        try {
            const country = await CountrySearch.search(query);
            
            if (country) {
                CountrySearch.renderCountry(country);
            } else {
                CountrySearch.showError();
            }
        } catch (error) {
            CountrySearch.hideLoading();
            CountrySearch.showError();
        }
    }
});
    
    // Настройки API (заглушка)
    document.getElementById('saveApiKey')?.addEventListener('click', function() {
        Notification.show('Ключ сохранен (но это не точно)');
    });
    
    document.getElementById('clearApiKey')?.addEventListener('click', function() {
        document.getElementById('apiKeyInput').value = '';
        Notification.show('Ключ очищен');
    });
    
    // Инициализация
    Wishlist.render();
});
// Добавь этот код в app.js после остального
document.getElementById('saveApiKey').addEventListener('click', function() {
    const apiKey = document.getElementById('apiKeyInput').value.trim();
    if (apiKey) {
        localStorage.setItem('openrouter_api_key', apiKey);
        Notification.show('API ключ сохранен!');
    } else {
        Notification.show('Введите API ключ', 'error');
    }
});

document.getElementById('clearApiKey').addEventListener('click', function() {
    localStorage.removeItem('openrouter_api_key');
    document.getElementById('apiKeyInput').value = '';
    Notification.show('API ключ очищен');
});

// Загрузи сохраненный ключ при загрузке
document.addEventListener('DOMContentLoaded', function() {
    const savedKey = localStorage.getItem('openrouter_api_key');
    if (savedKey) {
        document.getElementById('apiKeyInput').value = savedKey;
    }
});