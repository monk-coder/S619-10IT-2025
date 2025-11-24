// Менеджер игровой логики
class GameManager {
    constructor(app) {
        this.app = app;
        this.isClicking = false;
        this.clickEffectCount = 0;

        this.setupClickHandler();
    }

    setupClickHandler() {
        const clickArea = document.getElementById('click-area');
        const crystal = document.getElementById('crystal');

        clickArea.addEventListener('click', (e) => this.handleClick(e));

        // Добавляем эффект нажатия
        clickArea.addEventListener('mousedown', () => this.startClickAnimation());
        clickArea.addEventListener('touchstart', () => this.startClickAnimation());

        clickArea.addEventListener('mouseup', () => this.endClickAnimation());
        clickArea.addEventListener('touchend', () => this.endClickAnimation());
        clickArea.addEventListener('mouseleave', () => this.endClickAnimation());
    }

    startClickAnimation() {
        if (this.isClicking) return;

        this.isClicking = true;
        document.getElementById('crystal').style.transform = 'scale(0.95)';
    }

    endClickAnimation() {
        if (!this.isClicking) return;

        this.isClicking = false;
        document.getElementById('crystal').style.transform = 'scale(1)';
    }

    async handleClick(event) {
        if (!this.app.userData || this.app.userData.energy <= 0) {
            this.app.showNotification('Недостаточно энергии!', 'error');
            return;
        }

        // Создаем эффект клика
        this.createClickEffect(event);

        try {
            const response = await fetch(/api/click/${this.app.userId}, {
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

            // Обновляем данные приложения
            this.app.updateUserData({
                score: result.new_score,
                energy: result.new_energy,
                coins: result.new_coins,
                level: result.new_level
            });

            // Показываем достижения
            if (result.achievements && result.achievements.length > 0) {
                result.achievements.forEach(achievement => {
                    this.showAchievement(achievement);
                });
            }

            // Показываем уровень, если он повысился
            if (result.level_up) {
                this.showLevelUp(result.new_level);
            }

        } catch (error) {
            console.error('Error handling click:', error);
            this.app.showNotification('Ошибка соединения', 'error');
        }
    }

    createClickEffect(event) {
        const clickArea = document.getElementById('click-area');
        const effect = document.getElementById('click-effect');

        // Клонируем элемент эффекта
        const newEffect = effect.cloneNode(true);
        newEffect.style.display = 'block';

        // Устанавливаем позицию
        const rect = clickArea.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;

        newEffect.style.left = x + 'px';
        newEffect.style.top = y + 'px';

        // Устанавливаем текст в зависимости от улучшений
        const clickValue = this.app.userData.double_click;
        newEffect.textContent = +${clickValue};

        // Добавляем случайное смещение
        const offsetX = (Math.random() - 0.5) * 50;
        newEffect.style.setProperty('--offset-x', offsetX + 'px');

        clickArea.appendChild(newEffect);

        // Удаляем эффект после анимации
        setTimeout(() => {
            if (newEffect.parentNode) {
                newEffect.parentNode.removeChild(newEffect);
            }
        }, 1000);
    }

showAchievement(achievement) {
        const achievementNames = {
            'novice': { name: '🎉 Новичок', desc: '100 кликов!' },
            'hardworker': { name: '🔥 Трудяга', desc: '1000 кликов!' },
            'marathoner': { name: '🏆 Марафонец', desc: '7 дней подряд!' }
        };

        const achievementData = achievementNames[achievement] || { name: achievement, desc: '' };

        this.app.showNotification(${achievementData.name}\n${achievementData.desc}, 'success');

        // Вибрация, если доступна
        if (navigator.vibrate) {
            navigator.vibrate([100, 50, 100]);
        }
    }

    showLevelUp(newLevel) {
        this.app.showNotification(🎊 Уровень ${newLevel}!, 'success');

        // Специальные эффекты для уровней
        if (newLevel % 5 === 0) {
            this.celebrateLevelUp();
        }
    }

    celebrateLevelUp() {
        const crystal = document.getElementById('crystal');

        // Добавляем класс анимации
        crystal.classList.add('celebrating');

        // Удаляем класс после анимации
        setTimeout(() => {
            crystal.classList.remove('celebrating');
        }, 2000);

        // Показываем специальное уведомление
        this.app.tg.showPopup({
            title: '🎉 Новый уровень!',
            message: 'Поздравляем с достижением!',
            buttons: [{ type: 'ok' }]
        });
    }

    // Метод для автоматического сбора автокликером
    setupAutoClicker() {
        setInterval(() => {
            if (this.app.userData && this.app.userData.auto_clicker > 0) {
                this.showAutoClickEffect();
            }
        }, 1000);
    }

    showAutoClickEffect() {
        const clickArea = document.getElementById('click-area');
        const effect = document.createElement('div');

        effect.className = 'click-effect auto-click';
        effect.textContent = +${this.app.userData.auto_clicker} 🤖;
        effect.style.display = 'block';

        // Случайная позиция вокруг кристалла
        const angle = Math.random() * Math.PI * 2;
        const distance = 60 + Math.random() * 40;
        const x = 100 + Math.cos(angle) * distance;
        const y = 100 + Math.sin(angle) * distance;

        effect.style.left = x + 'px';
        effect.style.top = y + 'px';

        clickArea.appendChild(effect);

        setTimeout(() => {
            if (effect.parentNode) {
                effect.parentNode.removeChild(effect);
            }
        }, 1500);
    }
}