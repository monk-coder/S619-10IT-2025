document.addEventListener('DOMContentLoaded', function() {
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
    }
    
    async function handleSearch(e) {
        e.preventDefault();
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
        }
    }
    
    function saveApiKey() {
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (!apiKeyInput) return;
        
        const apiKey = apiKeyInput.value.trim();
        
        if (apiKey && apiKey !== '••••••••••••••••') {
            const success = AIService.saveApiKey(apiKey);
            if (success) {
                apiKeyInput.value = '••••••••••••••••';
                Notification.show('API ключ успешно сохранен!');
                updateApiStatus();
            } else Notification.show('Введите действительный API ключ', 'error');
        } else Notification.show('Введите API ключ', 'error');
    }
    
    function clearApiKey() {
        AIService.clearApiKey();
        const apiKeyInput = document.getElementById('apiKeyInput');
        if (apiKeyInput) apiKeyInput.value = '';
        Notification.show('API ключ очищен');
        updateApiStatus();
    }
    
    function initializeApiSettings() {
        const savedApiKey = AIService.getApiKey();
        const apiKeyInput = document.getElementById('apiKeyInput');
        
        if (!apiKeyInput) return;
        
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
        if (!statusElement) return;
        
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

    window.switchTab = switchTab;
    window.saveApiKey = saveApiKey;
    window.clearApiKey = clearApiKey;
});