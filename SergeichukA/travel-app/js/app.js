document.addEventListener('DOMContentLoaded', function() {
    console.log('Приложение загружается...');

    // Инициализация
    initializeApp();

    // Обработчики табов
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            switchTab(this.getAttribute('data-tab'));
        });
    });
    
    // Поиск стран
    document.getElementById('searchForm').addEventListener('submit', handleSearch);
    
    // Настройки API
    document.getElementById('saveApiKey').addEventListener('click', saveApiKey);
    document.getElementById('clearApiKey').addEventListener('click', clearApiKey);
    
    function initializeApp() {
        initializeApiSettings();
        Wishlist.render();
    }
    
    function switchTab(tabName) {
        // Убираем активные классы
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        // Добавляем активные классы
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        
        // Специальные действия для табов
        if (tabName === 'wishlist') {
            Wishlist.render();
        } else if (tabName === 'settings') {
            updateApiStatus();
        }
    }
    
    async function handleSearch(e) {
        e.preventDefault();
        const query = document.getElementById('searchInput').value.trim();
        
        if (query) {
            try {
                const country = await CountrySearch.search(query);
                
                if (country) {
                    CountrySearch.renderCountry(country);
                } else {
                    CountrySearch.showError();
                }
            } catch (error) {
                console.error('Ошибка поиска:', error);
                CountrySearch.showError();
            }
        }
    }
    
    function saveApiKey() {
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        
        if (apiKey && apiKey !== '••••••••••••••••') {
            const success = AIService.saveApiKey(apiKey);
            if (success) {
                document.getElementById('apiKeyInput').value = '••••••••••••••••';
                Notification.show('API ключ успешно сохранен!');
                updateApiStatus();
            } else {
                Notification.show('Введите действительный API ключ', 'error');
            }
        } else {
            Notification.show('Введите API ключ', 'error');
        }
    }
    
    function clearApiKey() {
        AIService.clearApiKey();
        document.getElementById('apiKeyInput').value = '';
        Notification.show('API ключ очищен');
        updateApiStatus();
    }
    
    function initializeApiSettings() {
        const savedApiKey = AIService.getApiKey();
        const apiKeyInput = document.getElementById('apiKeyInput');
        
        if (savedApiKey) {
            apiKeyInput.value = '••••••••••••••••';
            apiKeyInput.placeholder = 'API ключ сохранен';
        } else {
            apiKeyInput.value = '';
            apiKeyInput.placeholder = 'Введите ваш API ключ OpenRouter';
        }
        
        updateApiStatus();
    }
    
    function updateApiStatus() {
        const statusElement = document.getElementById('apiStatus');
        const testResult = AIService.testApiKey();
        
        if (testResult.valid) {
            statusElement.innerHTML = `
                <div style="color: var(--success); margin-top: 10px;">
                    <i class="fas fa-check-circle"></i> ${testResult.message}
                </div>
            `;
        } else {
            statusElement.innerHTML = `
                <div style="color: var(--secondary); margin-top: 10px;">
                    <i class="fas fa-exclamation-triangle"></i> ${testResult.message}
                </div>
            `;
        }
    }
});