
class Wishlist {
    static get() {
        if (!AuthService.isLoggedIn()) {
            return [];
        }

        try {
            const wishlistKey = AuthService.getUserWishlistKey();
            const wishlist = JSON.parse(localStorage.getItem(wishlistKey)) || [];
            return Array.isArray(wishlist) ? wishlist : [];
        } catch (error) {
            console.error('Ошибка загрузки вишлиста:', error);
            return [];
        }
    }
    
    static save(wishlist) {
        if (!AuthService.isLoggedIn()) {
            Notification.show('Войдите в систему для сохранения вишлиста', 'error');
            return;
        }

        const wishlistKey = AuthService.getUserWishlistKey();
        localStorage.setItem(wishlistKey, JSON.stringify(wishlist));
    }
    
    static add(countryData) {
        if (!AuthService.isLoggedIn()) {
            Notification.show('Войдите в систему для добавления в вишлист', 'error');
            return false;
        }

        const wishlist = this.get();
        
        const exists = wishlist.some(item => item.name === countryData.name);
        
        if (!exists) {
            wishlist.push(countryData);
            this.save(wishlist);
            Notification.show(`"${countryData.name}" добавлена в вишлист!`);
            this.render();
            return true;
        } else {
            Notification.show(`"${countryData.name}" уже в вишлисте!`, 'error');
            return false;
        }
    }
    
    static addFromSearch(countryData) {
        return this.add(countryData);
    }
    
    static remove(countryName) {
        if (!AuthService.isLoggedIn()) {
            Notification.show('Войдите в систему для управления вишлистом', 'error');
            return;
        }

        let wishlist = this.get();
        wishlist = wishlist.filter(item => item.name !== countryName);
        this.save(wishlist);
        this.render();
        Notification.show(`"${countryName}" удалена из вишлиста`);
    }
    
    static render() {
        const list = document.getElementById('wishlist-list');
        if (!list) return;
        
        if (!AuthService.isLoggedIn()) {
            list.innerHTML = `
                <div class="empty-wishlist">
                    <i class="fas fa-user-lock"></i>
                    <h3>Войдите в систему</h3>
                    <p>Для просмотра вашего вишлиста необходимо войти в систему.</p>
                    <button onclick="AuthUI.showLoginModal()" style="margin-top: 1rem;">
                        <i class="fas fa-sign-in-alt"></i> Войти
                    </button>
                </div>
            `;
            return;
        }

        const wishlist = this.get();
        
        if (wishlist.length === 0) {
            list.innerHTML = `
                <div class="empty-wishlist">
                    <i class="fas fa-compass"></i>
                    <h3>Ваш вишлист пуст</h3>
                    <p>Начните поиск стран и добавляйте их в свой список!</p>
                    <button onclick="switchTab('search')" style="margin-top: 1rem;">
                        <i class="fas fa-search"></i> Найти страны
                    </button>
                </div>
            `;
            return;
        }
        
        list.innerHTML = wishlist.map(country => `
            <div class="wishlist-item">
                <div class="wishlist-info">
                    <img src="${country.flag}" alt="Флаг ${country.name}" class="wishlist-flag">
                    <div class="wishlist-details">
                        <h3>${country.name}</h3>
                        <p>${country.capital} • ${country.region}</p>
                        <small>Население: ${country.population}</small>
                    </div>
                </div>
                <div class="wishlist-actions">
                    <button class="ai-guide-btn-small" onclick="Country.getAIGuide('${country.name.replace(/'/g, "\\'")}')">
                        <i class="fas fa-robot"></i> AI-гид
                    </button>
                    <button class="remove-btn" onclick="Wishlist.remove('${country.name.replace(/'/g, "\\'")}')">
                        <i class="fas fa-trash"></i> Удалить
                    </button>
                </div>
            </div>
        `).join('');
    }

    static clearCache() {
        // Очищаем кэш при выходе из системы
        this.render();
    }

static render() {
    const list = document.getElementById('wishlist-list');
    if (!list) return;
    
    if (!AuthService.isLoggedIn()) {
        list.innerHTML = `
            <div class="empty-wishlist">
                <i class="fas fa-user-lock"></i>
                <h3>Войдите в систему</h3>
                <p>Для просмотра вашего вишлиста необходимо войти в систему.</p>
                <a href="https://yandex.ru/video/preview/101741706696071987" target="_blank" style="margin-top: 1rem; display: inline-block;">
                    <button>
                        <i class="fas fa-sign-in-alt"></i> Войти
                    </button>
                </a>
            </div>
        `;
        return;
    }
    
}
}
window.Wishlist = Wishlist;
