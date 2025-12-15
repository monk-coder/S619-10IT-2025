class Wishlist {
<<<<<<< HEAD
    static get() {
        try {
            const wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
            return Array.isArray(wishlist) ? wishlist : [];
=======
    static baseURL = 'http://localhost:8000/api';

    static async get() {
        if (!AuthService.isLoggedIn()) return [];

        try {
            const apiKey = AuthService.getApiKey();
            const response = await fetch(`${this.baseURL}/wishlist`, {
                method: 'GET',
                headers: {'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json'}
            });

            if (!response.ok) throw new Error('Ошибка загрузки вишлиста');

            const data = await response.json();
            return data.wishlist || [];

>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
        } catch (error) {
            console.error('Ошибка загрузки вишлиста:', error);
            return [];
        }
    }
<<<<<<< HEAD
    
    static save(wishlist) {
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
    }
    
    static add(countryData) {
        const wishlist = this.get();
        
        const exists = wishlist.some(item => item.name === countryData.name);
        
        if (!exists) {
            wishlist.push(countryData);
            this.save(wishlist);
            Notification.show(`"${countryData.name}" добавлена в вишлист!`);
            this.render();
        } else {
            Notification.show(`"${countryData.name}" уже в вишлисте!`, 'error');
        }
    }
    
    static addFromSearch(countryData) {
        this.add(countryData);
    }
    
    static remove(countryName) {
        let wishlist = this.get();
        wishlist = wishlist.filter(item => item.name !== countryName);
        this.save(wishlist);
        this.render();
        Notification.show(`"${countryName}" удалена из вишлиста`);
    }
    
    static render() {
        const list = document.getElementById('wishlist-list');
        const wishlist = this.get();
        
        if (wishlist.length === 0) {
            list.innerHTML = `
                <div class="empty-wishlist">
                    <i class="fas fa-compass"></i>
                    <p>Ваш вишлист пуст. Начните поиск стран и добавляйте их в свой список!</p>
=======

    static async add(countryData) {
        if (!AuthService.isLoggedIn()) {
            Notification.show('Войдите в систему для добавления в вишлист', 'error');
            return false;
        }

        try {
            const apiKey = AuthService.getApiKey();
            const response = await fetch(`${this.baseURL}/wishlist`, {
                method: 'POST',
                headers: {'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json'},
                body: JSON.stringify(countryData)
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Ошибка добавления в вишлист');

            Notification.show(`"${countryData.name}" добавлена в вишлист!`);
            this.render();
            return true;

        } catch (error) {
            Notification.show(error.message, 'error');
            return false;
        }
    }

    static async remove(countryName) {
        if (!AuthService.isLoggedIn()) {
            Notification.show('Войдите в систему для управления вишлистом', 'error');
            return;
        }

        try {
            const apiKey = AuthService.getApiKey();
            const response = await fetch(`${this.baseURL}/wishlist/${encodeURIComponent(countryName)}`, {
                method: 'DELETE',
                headers: {'Authorization': `Bearer ${apiKey}`, 'Content-Type': 'application/json'}
            });

            const data = await response.json();

            if (!response.ok) throw new Error(data.error || 'Ошибка удаления из вишлиста');

            Notification.show(`"${countryName}" удалена из вишлиста`);
            this.render();

        } catch (error) { Notification.show(error.message, 'error'); }
    }

    static async render() {
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
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
                </div>
            `;
            return;
        }
<<<<<<< HEAD
        
        list.innerHTML = wishlist.map(country => `
            <div class="wishlist-item">
                <div class="wishlist-info">
                    <img src="${country.flag}" alt="Флаг ${country.name}" style="width: 60px; height: 40px; border-radius: 6px; object-fit: cover;">
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
}
=======

        try {
            const wishlist = await this.get();

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

        } catch (error) {
            list.innerHTML = `
                <div class="empty-wishlist">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Ошибка загрузки</h3>
                    <p>Не удалось загрузить ваш вишлист. Попробуйте позже.</p>
                </div>
            `;
        }
    }

    static clearCache() { this.render(); }
}

window.Wishlist = Wishlist;
>>>>>>> 858ccdf72c9072d46fc79832eb8653ed7fc0daa8
