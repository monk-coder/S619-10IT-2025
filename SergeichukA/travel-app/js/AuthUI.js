
class AuthUI {
    static init() {
        this.createAuthSection();
        this.bindAuthEvents();
        this.updateAuthUI();
    }

    static createAuthSection() {
        const header = document.querySelector('header');
        const existingAuthSection = document.getElementById('auth-section');
        
        if (existingAuthSection) {
            existingAuthSection.remove();
        }

        const authSection = document.createElement('div');
        authSection.id = 'auth-section';
        authSection.className = 'auth-section';
        header.appendChild(authSection);
    }

    static bindAuthEvents() {
        // Закрытие модального окна
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('close')) {
                this.hideAuthModal();
            }
        });

        // Клик вне модального окна
        document.getElementById('authModal').addEventListener('click', (e) => {
            if (e.target.id === 'authModal') {
                this.hideAuthModal();
            }
        });

        // Переключение между вкладками
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = tab.getAttribute('data-tab');
                this.switchAuthTab(tabName);
            });
        });

        // Форма входа
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Форма регистрации
        document.getElementById('registerForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
    }

    static switchAuthTab(tabName) {
        console.log('Switching to tab:', tabName);
        
        // Обновляем активные вкладки
        document.querySelectorAll('.auth-tab').forEach(tab => {
            tab.classList.toggle('active', tab.getAttribute('data-tab') === tabName);
        });

        // Обновляем активные формы
        document.querySelectorAll('.auth-form').forEach(form => {
            form.classList.toggle('active', form.id === `${tabName}Form`);
        });

        // Обновляем заголовок
        document.getElementById('authModalTitle').textContent = 
            tabName === 'login' ? 'Вход в систему' : 'Регистрация';
    }

    static async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;

        if (!username || !password) {
            Notification.show('Заполните все поля', 'error');
            return;
        }

        try {
            const user = await AuthService.login(username, password);
            Notification.show(`Добро пожаловать, ${user.username}!`);
            this.hideAuthModal();
            this.updateAuthUI();
            Wishlist.render();
        } catch (error) {
            Notification.show(error.message, 'error');
        }
    }

    static async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const email = document.getElementById('registerEmail').value;
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('registerConfirmPassword').value;

        if (!username || !email || !password || !confirmPassword) {
            Notification.show('Заполните все поля', 'error');
            return;
        }

        if (password !== confirmPassword) {
            Notification.show('Пароли не совпадают', 'error');
            return;
        }

        if (password.length < 6) {
            Notification.show('Пароль должен содержать минимум 6 символов', 'error');
            return;
        }

        try {
            const user = await AuthService.register(username, email, password);
            Notification.show(`Регистрация успешна! Добро пожаловать, ${username}!`);
            this.hideAuthModal();
            this.updateAuthUI();
            Wishlist.render();
        } catch (error) {
            Notification.show(error.message, 'error');
        }
    }

    static showLoginModal() {
        console.log('Showing login modal');
        this.switchAuthTab('login');
        document.getElementById('authModal').style.display = 'block';
    }

    static showRegisterModal() {
        console.log('Showing register modal');
        this.switchAuthTab('register');
        document.getElementById('authModal').style.display = 'block';
    }

    static hideAuthModal() {
        document.getElementById('authModal').style.display = 'none';
        // Очищаем формы
        document.querySelectorAll('.auth-form').forEach(form => form.reset());
    }

    static updateAuthUI() {
        const authSection = document.getElementById('auth-section');
        if (!authSection) return;

        const user = AuthService.getCurrentUser();

        if (user) {
            authSection.innerHTML = `
                <div class="user-info">
                    <i class="fas fa-user-circle"></i>
                    <span>${user.username}</span>
                    <button onclick="AuthUI.logout()" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> Выйти
                    </button>
                </div>
            `;
        } else {
            authSection.innerHTML = `
                <div class="auth-buttons">
                    <a href="https://yandex.ru/video/preview/101741706696071987" target="_blank" class="auth-btn login-btn">
                        <i class="fas fa-sign-in-alt"></i> Войти
                    </a>
                    <a href="https://yandex.ru/video/preview/101741706696071987" target="_blank" class="auth-btn register-btn">
                        <i class="fas fa-user-plus"></i> Регистрация
                    </a>
                </div>
            `;
        }
    }

    static logout() {
        AuthService.logout();
        Notification.show('Вы вышли из системы');
        this.updateAuthUI();
        Wishlist.render();
    }
}

// Делаем методы глобально доступными
window.AuthUI = AuthUI;
