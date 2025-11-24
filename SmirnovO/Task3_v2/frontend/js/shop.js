// Менеджер магазина
class ShopManager {
    constructor(app) {
        this.app = app;
        this.shopItems = {
            'double_click': {
                name: '💎 Двойной клик',
                price: 100,
                description: 'Получайте +2 очка за каждый клик',
                effect: 'Удваивает награду за клик'
            },
            'auto_clicker': {
                name: '🤖 Автокликер',
                price: 500,
                description: 'Автоматически получайте +1 очко в секунду',
                effect: 'Пассивный доход очков'
            },
            'max_energy': {
                name: '🔋 Больше энергии',
                price: 300,
                description: 'Увеличивает максимальную энергию до 200',
                effect: 'Больше кликов без перерыва'
            },
            'fast_recovery': {
                name: '⚡ Быстрое восстановление',
                price: 400,
                description: 'Энергия восстанавливается со скоростью 2/мин',
                effect: 'Быстрее возвращайтесь в игру'
            }
        };
    }

    loadShopItems() {
        const shopContainer = document.getElementById('shop-items');
        shopContainer.innerHTML = '';

        Object.entries(this.shopItems).forEach(([id, item]) => {
            const shopItem = this.createShopItem(id, item);
            shopContainer.appendChild(shopItem);
        });
    }

    createShopItem(id, item) {
        const element = document.createElement('div');
        element.className = 'shop-item';

        const userData = this.app.userData;
        const owned = this.isItemOwned(id, userData);
        const canAfford = userData.coins >= item.price;
        const canBuy = !owned && canAfford;

        element.innerHTML =
            <div class="shop-item-header">
                <div class="shop-item-name">${item.name}</div>
                <div class="shop-item-price">${item.price} 🪙</div>
            </div>
            <div class="shop-item-desc">${item.description}</div>
            <div class="shop-item-effect">${item.effect}</div>
            <button class="buy-btn" ${!canBuy ? 'disabled' : ''}>
                ${owned ? '✅ Куплено' : (canAfford ? 'Купить' : 'Недостаточно монет')}
            </button>
        ;

        const buyButton = element.querySelector('.buy-btn');
        if (canBuy) {
            buyButton.addEventListener('click', () => this.buyItem(id));
        }

        return element;
    }

    isItemOwned(itemId, userData) {
        switch (itemId) {
            case 'double_click':
                return userData.double_click > 1;
            case 'auto_clicker':
                return userData.auto_clicker > 0;
            case 'max_energy':
                return userData.max_energy > 100;
            case 'fast_recovery':
                return userData.fast_recovery > 1;
            default:
                return false;
        }
    }

    async buyItem(itemId) {
        if (!this.app.userData) return;

        try {
            const response = await fetch(/api/shop/${this.app.userId}/${itemId}, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const result = await response.json();

            if (result.error) {
                this.app.showNotification(result.error, 'error');
                return;
            }

            // Обновляем данные пользователя
            this.app.updateUserData({
                coins: result.new_coins
            });

            // Обновляем конкретные характеристики в зависимости от купленного предмета
            this.updateUserStats(itemId);

            this.app.showNotification(✅ Куплено: ${this.shopItems[itemId].name}, 'success');

            // Перезагружаем список товаров
            this.loadShopItems();

} catch (error) {
            console.error('Error buying item:', error);
            this.app.showNotification('Ошибка покупки', 'error');
        }
    }

    updateUserStats(itemId) {
        // Здесь можно обновить специфичные характеристики
        // Основные данные обновятся при следующей загрузке
        switch (itemId) {
            case 'max_energy':
                this.app.showNotification('Максимальная энергия увеличена до 200!', 'info');
                break;
            case 'fast_recovery':
                this.app.showNotification('Скорость восстановления увеличена!', 'info');
                break;
            case 'double_click':
                this.app.showNotification('Теперь вы получаете +2 очка за клик!', 'info');
                break;
            case 'auto_clicker':
                this.app.showNotification('Автокликер активирован! +1 очко/сек', 'info');
                break;
        }
    }
}