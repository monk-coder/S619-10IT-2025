class Wishlist {
    static get() {
        try {
            const wishlist = JSON.parse(localStorage.getItem('wishlist')) || [];
            return Array.isArray(wishlist) ? wishlist : [];
        } catch (error) {
            console.error('Ошибка загрузки вишлиста:', error);
            return [];
        }
    }
    
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
                </div>
            `;
            return;
        }
        
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