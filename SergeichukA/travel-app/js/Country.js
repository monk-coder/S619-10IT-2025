class Country {
    constructor(data) {
        this.data = data;
    }
    
    render() {
        const safeData = this.escapeHtml(JSON.stringify(this.data));
        
        return `
            <div class="country-card">
                <img src="${this.data.flag}" alt="Флаг ${this.data.name}" class="country-flag">
                <div class="country-info">
                    <h2 class="country-name">
                        <i class="fas fa-flag"></i> ${this.data.name}
                        <small>(${this.data.nativeName})</small>
                    </h2>
                    
                    <div class="country-detail">
                        <i class="fas fa-landmark"></i>
                        <strong>Столица:</strong> ${this.data.capital}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-globe-europe"></i>
                        <strong>Регион:</strong> ${this.data.region}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-users"></i>
                        <strong>Население:</strong> ${this.data.population}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-ruler-combined"></i>
                        <strong>Площадь:</strong> ${this.data.area}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-language"></i>
                        <strong>Языки:</strong> ${this.data.languages}
                    </div>
                    
                    <div class="country-detail">
                        <i class="fas fa-money-bill-wave"></i>
                        <strong>Валюта:</strong> ${this.data.currency}
                    </div>
                    
                    <div class="country-description">
                        <p><strong>Описание:</strong> ${this.data.description}</p>
                    </div>

                    <!-- AI Guide Section -->
                    <div class="ai-guide-section">
                        <button class="ai-guide-btn" onclick="Country.getAIGuide('${this.escapeHtml(this.data.name)}')">
                            <i class="fas fa-robot"></i> Получить AI-гид по стране
                        </button>
                        <div id="ai-guide-${this.data.name.replace(/\s+/g, '-')}" class="ai-guide-content"></div>
                    </div>
                    
                    <button class="add-to-wishlist" onclick="Wishlist.addFromSearch(${safeData})">
                        <i class="fas fa-heart"></i> Добавить в вишлист
                    </button>
                </div>
            </div>
        `;
    }

    static async getAIGuide(countryName) {
        console.log('Получение AI-гида для:', countryName);
        
        const wishlist = Wishlist.get();
        const country = wishlist.find(item => item.name === countryName);
        
        if (!country) {
            Notification.show('Сначала добавьте страну в вишлист', 'error');
            return;
        }

        const guideElement = document.getElementById(`ai-guide-${countryName.replace(/\s+/g, '-')}`);
        const button = guideElement.previousElementSibling;
        
        try {
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Генерируем гид...';
            button.disabled = true;
            guideElement.innerHTML = '';

            const guide = await AIService.getCountryGuide(countryName, country);
            
            guideElement.innerHTML = `
                <div class="ai-guide-card">
                    <h3><i class="fas fa-compass"></i> AI-Гид по ${countryName}</h3>
                    <div class="guide-content">${this.formatGuideText(guide)}</div>
                </div>
            `;
            
            button.innerHTML = '<i class="fas fa-robot"></i> Обновить AI-гид';
            button.disabled = false;
            
        } catch (error) {
            console.error('Ошибка при получении гида:', error);
            guideElement.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>Ошибка: ${error.message}</p>
                    <small>Проверьте ваш API ключ в настройках</small>
                </div>
            `;
            
            button.innerHTML = '<i class="fas fa-robot"></i> Попробовать снова';
            button.disabled = false;
        }
    }

    static formatGuideText(text) {
        return text.split('\n').map(line => {
            if (line.trim() === '') return '<br>';
            return `<p>${line}</p>`;
        }).join('');
    }

    escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
}