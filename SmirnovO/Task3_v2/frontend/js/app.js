// Основной файл приложения
class ClickerApp {
    constructor() {
        this.tg = window.Telegram.WebApp;
        this.userId = null;
        this.userData = null;
        this.isLoading = false;

        this.init();
    }

    init() {
        // Инициализация Telegram Web App
        this.tg.expand();
        this.tg.enableClosingConfirmation();

        // Получение user_id из URL
        this.userId = this.getUserIdFromUrl();

        if (!this.userId) {
            this.showError('User ID not found');
            return;
        }

        // Инициализация модулей
        this.game = new GameManager(this);
        this.shop = new ShopManager(this);
        this.ui = new UIManager(this);

        // Загрузка данных пользователя
        this.loadUserData();

        // Настройка авто-обновления
        this.setupAutoRefresh();

        // Показ уведомления о загрузке
        this.tg.showPopup({
            title: 'Добро пожаловать!',
            message: 'Игра загружается...',
            buttons: [{ type: 'ok' }]
        });
    }

    getUserIdFromUrl() {
        const path = window.location.pathname;
        const match = path.match(/\/game\/(\d+)/);
        return match ? parseInt(match[1]) : null;
    }

    async loadUserData() {
        if (this.isLoading) return;

        this.isLoading = true;
        this.ui.showLoading(true);

        try {
            const response = await fetch(/api/user/${this.userId});

            if (!response.ok) {
                throw new Error(HTTP error! status: ${response.status});
            }

            this.userData = await response.json();
            this.ui.updateUI(this.userData);

        } catch (error) {
            console.error('Error loading user data:', error);
            this.showError('Ошибка загрузки данных');
        } finally {
            this.isLoading = false;
            this.ui.showLoading(false);
        }
    }

    setupAutoRefresh() {
        // Обновление данных каждые 10 секунд
        setInterval(() => {
            this.loadUserData();
        }, 10000);

        // Обновление энергии каждую секунду (визуальное)
        setInterval(() => {
            if (this.userData && this.userData.energy < this.userData.max_energy) {
                this.ui.updateEnergyBar();
            }
        }, 1000);
    }

    showNotification(message, type = 'info') {
        this.ui.showNotification(message, type);
    }

    showError(message) {
        this.showNotification(message, 'error');
        console.error(message);
    }

    // Метод для обновления данных после действий
    updateUserData(newData) {
        this.userData = { ...this.userData, ...newData };
        this.ui.updateUI(this.userData);
    }
}

// Менеджер UI
class UIManager {
    constructor(app) {
        this.app = app;
        this.setupEventListeners();
    }

    setupEventListeners() {
        // Кнопки управления
        document.getElementById('shop-btn').addEventListener('click', () => this.showShop());
        document.getElementById('leaderboard-btn').addEventListener('click', () => this.showLeaderboard());
        document.getElementById('achievements-btn').addEventListener('click', () => this.showAchievements());
        document.getElementById('profile-btn').addEventListener('click', () => this.showProfile());

        // Закрытие модальных окон
        document.getElementById('close-shop').addEventListener('click', () => this.hideShop());
        document.getElementById('close-leaderboard').addEventListener('click', () => this.hideLeaderboard());
        document.getElementById('close-achievements').addEventListener('click', () => this.hideAchievements());

        // Закрытие по клику вне окна

window.addEventListener('click', (e) => {
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    updateUI(userData) {
        this.updateBasicInfo(userData);
        this.updateEnergyBar(userData);
        this.updateCrystalAppearance(userData);
    }

    updateBasicInfo(userData) {
        document.getElementById('username').textContent = userData.username || 'Игрок';
        document.getElementById('level').textContent = userData.level;
        document.getElementById('score').textContent = this.formatNumber(userData.score);
        document.getElementById('coins').textContent = this.formatNumber(userData.coins);
        document.getElementById('energy').textContent = userData.energy;
        document.getElementById('max-energy').textContent = userData.max_energy;
    }

    updateEnergyBar(userData = this.app.userData) {
        if (!userData) return;

        const energyFill = document.getElementById('energy-fill');
        const energyPercent = (userData.energy / userData.max_energy) * 100;
        energyFill.style.width = ${energyPercent}%;

        // Изменение цвета в зависимости от уровня энергии
        if (energyPercent < 20) {
            energyFill.style.background = 'linear-gradient(90deg, #ff6b6b, #ff8e53)';
        } else if (energyPercent < 50) {
            energyFill.style.background = 'linear-gradient(90deg, #ffa726, #ffca28)';
        } else {
            energyFill.style.background = 'linear-gradient(90deg, #4CAF50, #8BC34A)';
        }
    }

    updateCrystalAppearance(userData) {
        const crystal = document.getElementById('crystal');

        // Удаляем предыдущие классы уровней
        crystal.classList.remove('level-5', 'level-10', 'level-15');

        // Добавляем класс в зависимости от уровня
        if (userData.level >= 15) {
            crystal.classList.add('level-15');
        } else if (userData.level >= 10) {
            crystal.classList.add('level-10');
        } else if (userData.level >= 5) {
            crystal.classList.add('level-5');
        }
    }

    showLoading(show) {
        // Можно добавить индикатор загрузки
        if (show) {
            document.body.style.opacity = '0.7';
        } else {
            document.body.style.opacity = '1';
        }
    }

    showShop() {
        document.getElementById('shop-modal').style.display = 'block';
        this.app.shop.loadShopItems();
    }

    hideShop() {
        document.getElementById('shop-modal').style.display = 'none';
    }

    async showLeaderboard() {
        const modal = document.getElementById('leaderboard-modal');
        const leaderboardEl = document.getElementById('leaderboard');

        modal.style.display = 'block';
        leaderboardEl.innerHTML = '<div class="loading">Загрузка...</div>';

        try {
            const response = await fetch('/api/leaderboard');
            const leaders = await response.json();

            leaderboardEl.innerHTML = '';
            leaders.slice(0, 20).forEach(player => {
                const item = document.createElement('div');
                item.className = 'leaderboard-item';
                item.innerHTML =
                    <div class="leaderboard-rank">${player.rank}</div>
                    <div class="leaderboard-user">
                        <div class="leaderboard-name">${player.username || 'Аноним'}</div>
                        <div class="leaderboard-level">Ур. ${player.level}</div>
                    </div>
                    <div class="leaderboard-score">${this.formatNumber(player.score)}</div>
                ;
                leaderboardEl.appendChild(item);
            });

        } catch (error) {
            leaderboardEl.innerHTML = '<div class="error">Ошибка загрузки</div>';
            console.error('Error loading leaderboard:', error);
        }
    }

hideLeaderboard() {
        document.getElementById('leaderboard-modal').style.display = 'none';
    }

    async showAchievements() {
        const modal = document.getElementById('achievements-modal');
        const achievementsEl = document.getElementById('achievements-list');

        modal.style.display = 'block';
        achievementsEl.innerHTML = '<div class="loading">Загрузка...</div>';

        try {
            const response = await fetch(/api/achievements/${this.app.userId});
            const achievements = await response.json();

            achievementsEl.innerHTML = '';

            if (achievements.length === 0) {
                achievementsEl.innerHTML = '<div class="no-achievements">Достижений пока нет</div>';
                return;
            }

            const achievementNames = {
                'novice': { name: 'Новичок', desc: 'Сделать 100 кликов' },
                'hardworker': { name: 'Трудяга', desc: 'Сделать 1000 кликов' },
                'marathoner': { name: 'Марафонец', desc: 'Зайти в игру 7 дней подряд' }
            };

            achievements.forEach(achievement => {
                const achievementData = achievementNames[achievement] || { name: achievement, desc: '' };
                const item = document.createElement('div');
                item.className = 'achievement-item';
                item.innerHTML =
                    <div class="achievement-name">${achievementData.name}</div>
                    <div class="achievement-desc">${achievementData.desc}</div>
                ;
                achievementsEl.appendChild(item);
            });

        } catch (error) {
            achievementsEl.innerHTML = '<div class="error">Ошибка загрузки</div>';
            console.error('Error loading achievements:', error);
        }
    }

    hideAchievements() {
        document.getElementById('achievements-modal').style.display = 'none';
    }

    showProfile() {
        this.app.tg.showPopup({
            title: 'Профиль',
            message: Уровень: ${this.app.userData.level}\nОчки: ${this.formatNumber(this.app.userData.score)}\nМонеты: ${this.formatNumber(this.app.userData.coins)},
            buttons: [{ type: 'ok' }]
        });
    }

    showNotification(message, type = 'info') {
        const notifications = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = notification ${type};
        notification.textContent = message;

        notifications.appendChild(notification);

        // Автоматическое удаление через 3 секунды
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }
}

// Запуск приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.clickerApp = new ClickerApp();
});