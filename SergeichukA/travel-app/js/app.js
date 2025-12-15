document.addEventListener('DOMContentLoaded', function() {
<<<<<<< HEAD
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
=======
    initializeApp();

    function initializeApp() {
        AuthUI.init();
        initializeApiSettings();
        Wishlist.render();
        bindEventListeners();
        
        setTimeout(() => { AuthUI.updateAuthUI(); }, 100);
    }
    
    function bindEventListeners() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                switchTab(this.getAttribute('data-tab'));
            });
        });
        
        const searchForm = document.getElementById('searchForm');
        if (searchForm) searchForm.addEventListener('submit', handleSearch);
        
        const saveApiKey = document.getElementById('saveApiKey');
        const clearApiKey = document.getElementById('clearApiKey');
        
        if (saveApiKey) saveApiKey.addEventListener('click', saveApiKey);
        if (clearApiKey) clearApiKey.addEventListener('click', clearApiKey);
    }
    
    function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        
        const targetTab = document.querySelector(`[data-tab="${tabName}"]`);
        const targetContent = document.getElementById(`${tabName}-tab`);
        
        if (targetTab) targetTab.classList.add('active');
        if (targetContent) targetContent.classList.add('active');
        
        if (tabName === 'wishlist') Wishlist.render();
        else if (tabName === 'settings') updateApiStatus();
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
    }
    
    async function handleSearch(e) {
        e.preventDefault();
<<<<<<< HEAD
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
=======
        const searchInput = document.getElementById('searchInput');
        if (!searchInput) return;
        
        const query = searchInput.value.trim();
        
        if (query) {
            try {
                CountrySearch.showLoading();
                const country = await CountrySearch.search(query);
                
                if (country) CountrySearch.renderCountry(country);
                else CountrySearch.showError();
            } catch (error) {
                console.error('Ошибка поиска:', error);
                CountrySearch.showError();
            } finally { CountrySearch.hideLoading(); }
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
        }
    }
    
    function saveApiKey() {
<<<<<<< HEAD
        const apiKey = document.getElementById('apiKeyInput').value.trim();
=======
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (!apiKeyInput) return;
        
        const apiKey = apiKeyInput.value.trim();
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
        
        if (apiKey && apiKey !== '••••••••••••••••') {
            const success = AIService.saveApiKey(apiKey);
            if (success) {
<<<<<<< HEAD
                document.getElementById('apiKeyInput').value = '••••••••••••••••';
                Notification.show('API ключ успешно сохранен!');
                updateApiStatus();
            } else {
                Notification.show('Введите действительный API ключ', 'error');
            }
        } else {
            Notification.show('Введите API ключ', 'error');
        }
=======
                apiKeyInput.value = '••••••••••••••••';
                Notification.show('API ключ успешно сохранен!');
                updateApiStatus();
            } else Notification.show('Введите действительный API ключ', 'error');
        } else Notification.show('Введите API ключ', 'error');
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
    }
    
    function clearApiKey() {
        AIService.clearApiKey();
<<<<<<< HEAD
        document.getElementById('apiKeyInput').value = '';
=======
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (apiKeyInput) apiKeyInput.value = '';
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
        Notification.show('API ключ очищен');
        updateApiStatus();
    }
    
    function initializeApiSettings() {
        const savedApiKey = AIService.getApiKey();
        const apiKeyInput = document.getElementById('apiKeyInput');
        
<<<<<<< HEAD
=======
        if (!apiKeyInput) return;
        
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
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
<<<<<<< HEAD
=======
        if (!statusElement) return;
        
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
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
<<<<<<< HEAD
=======

    window.switchTab = switchTab;
    window.saveApiKey = saveApiKey;
    window.clearApiKey = clearApiKey;
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
});