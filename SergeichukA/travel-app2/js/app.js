document.addEventListener('DOMContentLoaded', function() {
    function initializeApp() {
        AuthUI.init();
        initializeApiSettings();
        Wishlist.render();
        bindEventListeners();
        setTimeout(() => AuthUI.updateAuthUI(), 100);
    }
    
    function bindEventListeners() {
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', function() {
                switchTab(this.getAttribute('data-tab'));
            });
        });
        document.getElementById('searchForm').addEventListener('submit', handleSearch);
        document.getElementById('saveApiKey').addEventListener('click', saveApiKey);
        document.getElementById('clearApiKey').addEventListener('click', clearApiKey);
    }
    
    function switchTab(tabName) {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        document.getElementById(`${tabName}-tab`).classList.add('active');
        if (tabName === 'wishlist') Wishlist.render();
        else if (tabName === 'settings') updateApiStatus();
    }
    
    async function handleSearch(e) {
        e.preventDefault();
        const query = document.getElementById('searchInput').value.trim();
        if (query) {
            try {
                CountrySearch.showLoading();
                const country = await CountrySearch.search(query);
                country ? CountrySearch.renderCountry(country) : CountrySearch.showError();
            } catch (error) {
                console.error('Ошибка поиска:', error);
                CountrySearch.showError();
            } finally { CountrySearch.hideLoading(); }
        }
    }
    
    function saveApiKey() {
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        if (apiKey && apiKey !== '••••••••••••••••') {
            if (AIService.saveApiKey(apiKey)) {
                document.getElementById('apiKeyInput').value = '••••••••••••••••';
                Notification.show('API ключ успешно сохранен!');
                updateApiStatus();
            } else Notification.show('Введите действительный API ключ', 'error');
        } else Notification.show('Введите API ключ', 'error');
    }
    
    function clearApiKey() {
        AIService.clearApiKey();
        document.getElementById('apiKeyInput').value = '';
        Notification.show('API ключ очищен');
        updateApiStatus();
    }
    
    function initializeApiSettings() {
        const apiKeyInput = document.getElementById('apiKeyInput');
        const savedApiKey = AIService.getApiKey();
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
        statusElement.innerHTML = testResult.valid 
            ? `<div style="color: var(--success); margin-top: 10px;"><i class="fas fa-check-circle"></i> ${testResult.message}</div>`
            : `<div style="color: var(--secondary); margin-top: 10px;"><i class="fas fa-exclamation-triangle"></i> ${testResult.message}</div>`;
    }

    window.switchTab = switchTab;
    window.saveApiKey = saveApiKey;
    window.clearApiKey = clearApiKey;
    
    initializeApp();
});