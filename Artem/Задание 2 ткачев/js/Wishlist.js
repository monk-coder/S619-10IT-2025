class Wishlist {
    static get() {
        return JSON.parse(localStorage.getItem('wishlist')) || [];
    }
    
    static save(wishlist) {
        localStorage.setItem('wishlist', JSON.stringify(wishlist));
    }
    
    static add(countryName) {
        const wishlist = this.get();
        if (!wishlist.includes(countryName)) {
            wishlist.push(countryName);
            this.save(wishlist);
            Notification.show(`"${countryName}" добавлена в вишлист!`);
        } else {
            Notification.show(`"${countryName}" уже в вишлисте!`, 'error');
        }
    }
    
    static remove(countryName) {
        let wishlist = this.get();
        wishlist = wishlist.filter(name => name !== countryName);
        this.save(wishlist);
        this.render();
        Notification.show(`"${countryName}" удалена из вишлиста`);
    }
    
    static render() {
        const list = document.getElementById('wishlist-list');
        let wishlist = this.get();
        
        if (!wishlist || !Array.isArray(wishlist)) {
            wishlist = [];
            this.save(wishlist);
        }
        
        if (wishlist.length === 0) {
            list.innerHTML = `
                <li class="empty-wishlist">
                    <i class="fas fa-compass"></i>
                    <p>Ваш вишлист пуст. Начните поиск стран и добавляйте их в свой список!</p>
                </li>
            `;
            return;
        }
        
        list.innerHTML = wishlist.map(countryName => {
            return `
                <li class="wishlist-item">
                    <div class="wishlist-info">
                        <img src="https://flagcdn.com/w320/${this.getCountryCode(countryName)}.png" alt="Флаг ${countryName}" style="width: 50px; height: 32px; border-radius: 6px;">
                        <div class="wishlist-details">
                            <h3>${countryName}</h3>
                            <p>Добавлена в вишлист</p>
                        </div>
                    </div>
                    <button class="remove-btn" onclick="Wishlist.remove('${countryName}')">
                        <i class="fas fa-trash"></i> Удалить
                    </button>
                </li>
            `;
        }).join('');
    }
    
    static getCountryCode(countryName) {
        const codes = {
            'Россия': 'ru',
            'США': 'us',
            'Франция': 'fr',
            'Германия': 'de',
            'Япония': 'jp',
            'Китай': 'cn',
            'Бразилия': 'br',
            'Италия': 'it',
            'Испания': 'es',
            'Великобритания': 'gb'
        };
        return codes[countryName] || 'un';
    }
}